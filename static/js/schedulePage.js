const app = Vue.createApp({
    data() {
        return {
            managedGames: [], // managed games filtered from allGames (already sorted)
            allGames: [], // All fetched games from the backend (already sorted)
            filteredGames: [], // Games to display in the table (filtered by team)
            expandedGameId: null, // ID of the currently expanded game card
            managedTeams: [], // Managed teams
            followedTeams: [], // Followed teams
            selectedTeams: [], // Teams selected for inclusion in the table
            isLoading: true, // Show a loading indicator while fetching games
            showReasonPopup: false, // Controls popup visibility
            popupReason: "", // Stores the reason to display in the popup
            selectedGame: null, // To store the game details for the modal
            showPlayedGames: false, // Controls whether played games are shown 
        };
    },
    methods: {
        fetchGamesAndCompare() {
            this.isLoading = true;
    
            // Fetch Tulospalvelu.fi and Jopox data in parallel
            Promise.all([
                fetch('/api/schedules').then(response => response.json()),
                fetch('/api/jopox_games').then(response => response.json())
            ])
            .then(([tulospalveluGames, jopoxGames]) => {
                // Save Tulospalvelu.fi data for rendering game cards
                if (Array.isArray(tulospalveluGames)) {
                    // Filter out duplicate Game IDs
                    const uniqueGames = [];
                    const seenGameIDs = new Set();
                    for (const game of tulospalveluGames) {
                        if (!seenGameIDs.has(game['Game ID'])) {
                            seenGameIDs.add(game['Game ID']);
                            uniqueGames.push(game);
                        }
                    }
                    this.allGames = uniqueGames;
                    this.managedGames = uniqueGames.filter(game => game.Type === 'manage');

                } else {
                    console.error('Unexpected Tulospalvelu response:', tulospalveluGames);
                }
                console.log('jopoxGames:', jopoxGames.data  );
                                // Send data to backend for comparison
                return fetch('/api/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tulospalvelu_games: this.managedGames, // Only unique and managed games sent for comparison
                        jopox_games: jopoxGames.data, // Assuming Jopox data is in `.data`
                    }),
                });
            })
            .then(response => response.json())
            .then(comparisonResults => {
                // Update game cards with comparison results
                console.log('Comparison results:', comparisonResults);
                this.managedGames = this.managedGames.map(game => {
                    const match = comparisonResults.find(
                        result => result.game['Game ID'] === game['Game ID']
                    );
                    return {
                        ...game,
                        match_status: match?.match_status || 'red', // Default to red if no match
                        reason: match?.reason || 'No match found',
                        best_match: match?.best_match || null, // Include best_match details if available
                        uid: match?.best_match?.Uid || null, // Include unique UID for later use
                        warning: match?.warning || null, // Include warning if available
                    };
                });
                this.allGames = this.allGames.map(game => {
                    const managedGame = this.managedGames.find(
                        managed => managed['Game ID'] === game['Game ID']
                    );
                    if (managedGame) {
                        // Jos peli löytyy managedGames-listasta, käytä päivitettyjä tietoja
                        return { ...game, ...managedGame };
                    }
                    return game; // Muuten pidä alkuperäinen
                });

                this.filterGames();
            })
            .catch(error => {
                console.error('Error during fetching or comparison:', error);
            })
            .finally(() => {
                this.isLoading = false;
            });
        },

        fetchTeams() {
            fetch('/api/teams')
                .then(response => response.json())
                .then(data => {
                    this.managedTeams = data.managed_teams; // Includes 'team_id'
                    this.followedTeams = data.followed_teams; // Includes 'team_id'
                    // Default selection uses 'team_id'
                    this.selectedTeams = data.managed_teams.map(team => team.team_id);
                    this.filterGames(); // Immediately filter games based on managed teams
                })
                .catch(error => {
                    console.error('Error fetching teams:', error);
                });
        },
        

        toggleTeam(team_id) {
            if (this.selectedTeams.includes(team_id)) {
                this.selectedTeams = this.selectedTeams.filter(id => id !== team_id);
            } else {
                this.selectedTeams.push(team_id);
            }
            this.filterGames(); // Update the table with new selection
        },

        togglePlayedGames() {
            this.showPlayedGames = !this.showPlayedGames;
            this.filterGames(); // Reapply filtering
        },
        
        filterGames() {
            if (!this.allGames || this.allGames.length === 0) {
                this.filteredGames = [];
                return;
            }
        
            if (this.selectedTeams.length === 0) {
                this.filteredGames = [];
                return;
            }
        
            // Filter games based on selected teams
            let filtered = this.allGames.filter(game =>
                this.selectedTeams.includes(String(game['Team ID']))
            );
        
            // Further filter out played games if `showPlayedGames` is false
            if (!this.showPlayedGames) {
                filtered = filtered.filter(game => {
                    const gameDateTime = new Date(`${game.Date} ${game.Time}`);
                    const now = new Date();
                    return gameDateTime > now; // Include only upcoming games
                });
            }
        
            this.filteredGames = filtered;
        },

        toggleGameDetails(gameId) {
            this.expandedGameId = this.expandedGameId === gameId ? null : gameId;
        },    
        
        showReason(reason) {
            if (reason) {
                alert(reason); // Display the reason for yellow or red status
            }
        },
    
        getButtonColor(teamName) {
            const colorMap = {
                musta: '#282828', // Light Gray
                punainen: '#ff5151', // Light Red
                sininen: '#2c778f', // Light Blue
                keltainen: '#ffff08', // Light Yellow
                valkoinen: '#cccccc', // Light White
                vihreä: '#137f13', // Light Green
            };
        
            const lowerCaseName = teamName.toLowerCase();
            for (const [key, value] of Object.entries(colorMap)) {
                if (lowerCaseName.includes(key)) {
                    return value; // Return the color if found
                }
            }
            return '#E0E0E0'; // Default light gray
        },
        
        getTextColor(backgroundColor, isSelected) {
            // Explicit override for very dark colors like black
            if (backgroundColor === '#282828') {
                return isSelected ? 'white' : '#E0E0E0'; // White text when selected, light gray when unselected
            }
        
            // Calculate contrast for other colors
            const color = backgroundColor.replace('#', '');
            const r = parseInt(color.substring(0, 2), 16);
            const g = parseInt(color.substring(2, 4), 16);
            const b = parseInt(color.substring(4, 6), 16);
            const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        
            // If unselected, always use darker text for visibility
            if (!isSelected) {
                return brightness > 155 ? 'black' : '#444444'; // Use slightly darker gray for better contrast
            }
        
            // Return white for dark backgrounds and black for light backgrounds when selected
            return brightness > 155 ? 'black' : 'white';
        },
        getRowStyle(game) {
            // Check if the game belongs to a managed team
            const isManaged = this.managedTeams.some(team => team.team_id === game['Team ID']);
            const isFollowed = this.followedTeams.some(team => team.team_id === game['Team ID']);
            
            const isBetweenManagedTeams =
                this.managedTeams.some(team => team.team_id === game['Home Team ID']) &&
                this.managedTeams.some(team => team.team_id === game['Away Team ID']);

            if (isBetweenManagedTeams) {
                return {
                    backgroundColor: '#ffffcc', // Highlight color for games between managed teams
                    color: '#000000',
                };
            }

            if (isManaged) {
                // Use the team-specific color for managed teams
                const backgroundColor = this.getButtonColor(game['Team Name']);
                const textColor = this.getTextColor(backgroundColor, true); // Adjust text color for contrast
                return {
                    backgroundColor: backgroundColor,
                    color: textColor,
                };
            } else if (isFollowed) {
                // Default color for followed teams
                return {
                    backgroundColor: '##ffffff', // Default light gray for followed teams
                    color: '#000000', // Black text for better contrast
                };
            }
        
            // Default styles if no match
            return {
                backgroundColor: 'transparent',
                color: '#000000',
            };
        },

        getDayName(sortableDate) {
            if (!sortableDate || typeof sortableDate !== 'string') {
                return 'Invalid Day';
            }
        
            // Map English day abbreviations to Finnish
            const dayMap = {
                Sat: 'La', // Saturday
                Sun: 'Su', // Sunday
                Mon: 'Ma', // Monday
                Tue: 'Ti', // Tuesday
                Wed: 'Ke', // Wednesday
                Thu: 'To', // Thursday
                Fri: 'Pe', // Friday
            };
        
            // Extract the day abbreviation (first three characters)
            const englishDay = sortableDate.split(',')[0];
            return dayMap[englishDay] || 'Invalid Day'; // Use the map or return a fallback
        },

        isPastDay(sortableDate) {
            try {
                const date = new Date(sortableDate);
                const now = new Date();
        
                // Vertaa vain päivää (ei aikaa)
                return date.setHours(0, 0, 0, 0) < now.setHours(0, 0, 0, 0);
            } catch (error) {
                console.error('Error parsing date:', sortableDate, error);
                return false;
            }
        },                       
                
        isTeamSelected(teamName) {
            // Check if a team is selected
            return this.selectedTeams.includes(teamName);
        },

        isNotManagedTeam(game) {
            return !this.managedTeams.some(team => team.team_id === game['Team ID']);
        },

        toggleReason(game) {
            if (game.reason) {
                this.popupReason = game.reason.replace(/\. /g, '<br>'); // Format the reason
                this.showReasonPopup = true; // Show modal
            }
        },
        
        showModal(event, reason) {
            if (!reason) {
                console.error("No reason provided for modal");
                return;
            }
            this.popupReason = reason;
        
            this.$nextTick(() => {
                const modal = document.querySelector(".modal-window");
        
                if (!modal) {
                    console.error("Modal element not found");
                    return;
                }

                if (this.showReasonPopup && this.popupReason === reason) {
                    this.closeModal();
                    return;
                }
            
        
                // Hanki kursorin sijainti
                const cursorX = event.clientX;
                const cursorY = event.clientY;
                console.log("Cursor position:", cursorX, cursorY);
        
                // Näytä modal-ikkuna tilapäisesti mittojen laskemista varten
                modal.style.visibility = "hidden";
                modal.style.display = "block";
        
                const modalWidth = modal.offsetWidth;
                const modalHeight = modal.offsetHeight;
        
                // Lasketaan modalin sijainti
                const scrollX = window.scrollX || window.pageXOffset;
                const scrollY = window.scrollY || window.pageYOffset;
        
                const arrowOffsetX = 0.05 * modalWidth; // Nuolen 5% offset modalin oikeasta reunasta
                const arrowOffsetY = 0.2 * modalHeight; // Nuolen 10% offset modalin alareunasta
                const topPosition = cursorY + scrollY + arrowOffsetY + 8 ; // Modalin alareuna siirtyy ylöspäin
                const leftPosition = cursorX + scrollX - (modalWidth - arrowOffsetX); // Modalin sijainti suhteessa nuoleen
                
                modal.style.position = "absolute";
                modal.style.top = `${topPosition}px`;
                modal.style.left = `${leftPosition}px`;
        
                // Näytä modal
                modal.style.visibility = "visible";
                modal.style.display = "block";
                this.showReasonPopup = true;
        
                console.log("Modal positioned at:", modal.style.top, modal.style.left);
            });
        },
        
        toggleModal(event, reason) {
            // Jos modal on jo auki ja syy on sama, sulje modal
            if (this.showReasonPopup && this.popupReason === reason) {
                this.closeModal();
            } else {
                // Muuten avaa modal uudelleen
                this.showModal(event, reason);
            }
        },             
                
       
        
        closeModal() {
            console.log("Modal closed"); // Debugging log
            this.showReasonPopup = false; // Hide the modal
            this.popupReason = ''; // Clear the reason text
        },
            

        formatReason(reason) {
            if (reason) {
                // Replace ". " with a line break
                return reason.replace(/\. /g, '<br>');
            }
            return '';
        },

    },
    
    computed: {
        groupedGames() {
            const groups = {};
        
            this.filteredGames.forEach(game => {
                const date = game.SortableDate; // Use SortableDate for grouping
                if (!groups[date]) {
                    groups[date] = [];
                }
                groups[date].push(game);
            });
        
            return groups;
        },
    },
    
    
    mounted() {
        this.fetchTeams(); // Fetch teams first
        this.fetchGamesAndCompare(); // Fetch games and run comparison

    },

template: 
`
<div class="container my-4">
    <div>
        <h1>Valittujen joukkueiden ohjelma Tulospalvelusta.</h1>
        <p> Tässä näkymässä esitetään oletuksena hallinnoimiesi joukkueiden otteluohjelma.</p>
        <p> Valitse näytettävät joukkueet painikkeista.</p>
    </div>
</div>

    
    <!-- Sticky Team Selector -->
<div class="sticky-team-selector">              
    <!-- Managed Teams -->
    <h1>Hallinnoimasi joukkueet</h1>
    <div class="btn-group">
        <button
            v-for="team in managedTeams"
            :key="team.team_id"
            @click="toggleTeam(team.team_id)"
            :style="{
                backgroundColor: getButtonColor(team.team_name),
                color: getTextColor(getButtonColor(team.team_name), isTeamSelected(team.team_id)),
                }"
            :class="['btn', isTeamSelected(team.team_id) ? 'selected-team' : 'unselected-team']"
        >
            {{ team.team_name }}<br>{{ team.stat_group}}
        </button>
    </div>
    
    <!-- Followed Teams -->
    <h1>Seuraamasi joukkueet</h1>
    <div class="btn-group">
        <button
            v-for="team in followedTeams"
            :key="team.team_id"
            @click="toggleTeam(team.team_id)"
            :style="{
                backgroundColor: getButtonColor(team.team_name),
                color: getTextColor(getButtonColor(team.team_name), isTeamSelected(team.team_id)),
            }"
            :class="['btn', isTeamSelected(team.team_id) ? 'selected-team' : 'unselected-team']"
        >
            {{ team.team_name }}<br>{{ team.stat_group }}
        </button>
    </div> 
    <div>
        <button class toggle-played-button @click="togglePlayedGames">
            {{ showPlayedGames ? "Piilota pelatut" : "Näytä pelatut" }}
        </button>
    </div>
</div>

<!-- Loading Indicator -->
<div v-if="isLoading" class="my-4">
    <p>Loading games...</p>
</div>

<div
    v-for="(games, date) in groupedGames"
    :key="date"
    class="game-window"
>
    <!-- Card Header -->
    <div 
        class="window-header"
        :class="{ 'past-day': isPastDay(date) }"
    >
        {{ getDayName(date) }} {{ games[0].Date }}
    </div>

    <!-- Game Info Cards -->
    <div class="game-cards">
    <div
        v-for="game in games"
        :key="game['Game ID'] + '-' + game['Team ID']"
        class="game-card"
        :style="getRowStyle(game)"
        @click="toggleGameDetails(game['Game ID'])"
    >
        <div class="gameInfo1">
            <div class="topRow">
                <p class="gameTeams">
                    {{ game['Home Team'] }} - {{ game['Away Team'] }}
                    <span v-if="game['Small Area Game'] === '1'">(Pienpeli)</span>
                </p>
                <div class="status-box"
                     v-if="!isPastDay(date) && !isNotManagedTeam(game)"
                     @click.stop="toggleModal($event, game.reason)"
                >
                    <span class="status-text">Jopox:</span>
                    <!-- Circle to indicate game status -->
                    <span
                        class="status-circle"
                        :class="{
                            'circle-green': game.match_status === 'green',
                            'circle-yellow': game.match_status === 'yellow',
                            'circle-red': game.match_status === 'red',
                        }"
                    ></span>
                </div>
            </div>
            <div class="bottomRow">
                <p class="gameTime"> Klo {{ game.Time || 'Aika ei saatavilla' }}</p>
                <p class="gameLocation">{{ game.Location || 'Paikka ei saatavilla' }}</p>
                <p class="gameStatgroup">{{ game['Level Name'] }}</p>
            </div>

            <!-- Expanded Section for Jopox Details -->
            <div v-if="expandedGameId === game['Game ID']" class="game-details">
                <h2>Jopox tapahtuma:</h2>
                <p><strong>{{ game.best_match?.Tapahtuma|| 'Not available' }}</strong></p>
                <p><strong>Paikka:</strong> {{ game.best_match?.Paikka || 'Not available' }}</p>
                <p><strong>Klo:</strong> {{ game.best_match?.Aika || 'Not available' }}</p>
                <p><strong>Lisätiedot:</strong> {{ game.best_match?.Lisätiedot || 'No additional details available' }}</p>

                <div v-if="game.warning" class="warning-message">
                <strong>Varoitus:</strong> {{ game.warning }}
                </div>

            </div>
        </div>
    </div>
</div>
</div>

<!-- Modal -->
<div v-show="showReasonPopup" class="modal-window">
    <div class="modal-arrow"></div>
    <span class="modal-close" @click.stop="closeModal">&times;</span>
    <h1>Jopox huomiot:</h1>
    <p v-html="popupReason"></p>
</div>



`
});

// Mount the Vue app
app.mount('#schedule-app');