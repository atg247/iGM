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
            showUpdateJopoxModal: false, // Päivitä Jopox -modalin näkyvyys
            form: {
                league_selected: '',
                league_options: [],
                event_selected: '',
                event_options: [],
                SiteNameLabel: '',
                HomeTeamTextbox: '',
                guest_team: '',
                AwayCheckbox: false,
                game_location: '',
                game_date: '',
                game_start_time: '',
                game_duration: '',
                game_public_info: ''
            }
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
            .then(([tulospalveluData, jopoxGames]) => {
                // Save Tulospalvelu.fi data for rendering game cards
                if (tulospalveluData && Array.isArray(tulospalveluData.managed_games)) {
                    console.log('Tulospalvelu data:', tulospalveluData);

                    const tulospalveluGames = tulospalveluData.managed_games;  // Käytetään oikeaa kenttää
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
                    console.error('Unexpected Tulospalvelu response:', tulospalveluData);
                }
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
                    try {
                        const gameDateTime = new Date(game.SortableDate); // Use SortableDate for comparison
                        const now = new Date();
        
                        // Compare only the day (ignore time)
                        const gameDateWithoutTime = new Date(
                            gameDateTime.getFullYear(),
                            gameDateTime.getMonth(),
                            gameDateTime.getDate()
                        );
                        const nowWithoutTime = new Date(
                            now.getFullYear(),
                            now.getMonth(),
                            now.getDate()
                        );
        
                        return gameDateWithoutTime >= nowWithoutTime; // Include only current and future games
                    } catch (error) {
                        console.error('Error filtering game by date:', game, error);
                        return false; // Exclude games with invalid dates
                    }
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
                const date = new Date(sortableDate); // Parse SortableDate
                const now = new Date();
        
                // Compare days only
                const dateWithoutTime = new Date(
                    date.getFullYear(),
                    date.getMonth(),
                    date.getDate()
                );
                const nowWithoutTime = new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    now.getDate()
                );
                
                return dateWithoutTime < nowWithoutTime;
            } catch (error) {
                console.error('Error parsing SortableDate:', sortableDate, error);
                return false; // Default to "not past" in case of an error
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
            this.showReasonPopup = false; // Hide the modal
            this.popupReason = ''; // Clear the reason text
        },
        
        openUpdateModal(game) {
            this.selectedGame = game; // Tallenna valittu peli
        
            // Lähetä backendiin pyyntö hakea olemassa olevat jopox-tiedot best matchin uid:llä
            const uid = game.best_match.Uid;
            console.log('haetaan tietoja uid:llä:', uid);
            fetch(`/api/jopox_form_information?uid=${uid}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                // Populate the form with the fetched data
                this.form.league_selected = data.league_selected || '';
                this.form.league_options = data.league_options || []; 
                if (this.form.league_selected && !this.form.league_options.includes(this.form.league_selected)) {
                    this.form.league_options.push(this.form.league_selected);
                }
                    
                this.form.event_selected = data.event_selected || '';
                this.form.event_options = data.event_options || [];
                this.form.SiteNameLabel = data.SiteNameLabel || '';
                this.form.HomeTeamTextbox = data.HomeTeamTextbox || '';
                this.form.guest_team = data.guest_team || '';
                this.form.AwayCheckbox = data.AwayCheckbox || false;
                this.form.game_location = data.game_location || '';
                this.form.game_date = data.game_date || '';
                this.form.game_start_time = data.game_start_time || '';
                this.form.game_duration = data.game_duration || '';
                this.form.game_public_info = data.game_public_info || '';

                console.log('Fetched Jopox data:', data);
                this.showUpdateJopoxModal = true; // Näytä Päivitä Jopox -modal
            })
            .catch(error => {
                console.error('Error fetching Jopox data:', error);
            });
        },
    
        // Lähetä tiedot backendille päivitystä varten
        updateJopox() {
            const payload = {
                game: this.selectedGame, // Tulospalvelun tiedot
                best_match: this.selectedGame.best_match, // Jopoxin tiedot
            };        
            fetch('/api/update_jopox', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            .then(response => response.json())
            .then(data => {
                alert('Jopox-päivitys onnistui: ' + data.message);
                this.closeUpdateModal(); // Sulje modal päivityksen jälkeen
            })
            .catch(error => {
                console.error('Virhe Jopox-päivityksessä:', error);
                alert('Päivityksessä tapahtui virhe.');
            });
        },
    
        // Sulje Päivitä Jopox -modal
        closeUpdateModal() {
            this.showUpdateJopoxModal = false;
            this.selectedGame = null;
        },

        formatReason(reason) {
            if (reason) {
                // Replace ". " with a line break
                return reason.replace(/\. /g, '<br>');
            }
            return '';
        },

        submitForm() {
            // Handle form submission logic here
            console.log('Form submitted:', this.form);
            this.closeUpdateModal();
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
                <button class="update-jopox-btn"
                v-if="!isPastDay(date) && !isNotManagedTeam(game)"
                @click.stop="openUpdateModal(game)">
                    <span class="status-text">Päivitä Jopox</span>
                </button>
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

<!-- Add this to your HTML or Vue template -->
<div v-if="showUpdateJopoxModal" class="modal-window2">
    <div class="modal-content">
        <span class="close" @click="closeUpdateModal">&times;</span>
        <h2>Päivitä Jopox</h2>
        <form id="jpx-details-form">
            <!-- Sarja -->
            <div>
                <label for="league">Sarja:</label>
                <select id="league" v-model="form.league_selected">
                    <!-- Luo vaihtoehdot ja valitse oikea oletusarvo -->
                    <option v-for="option in form.league_options" :key="option" :value="option">
                        {{ option }}
                    </option>
                </select>
            </div>

            <!-- Kotijoukkue -->
            <div>
                <label for="home_team">Joukkue: {{form.SiteNameLabel}}</label>
                <input type="text" id="home_team" v-model="form.HomeTeamTextbox" placeholder="Kotijoukkue">
            </div>

            <!-- Vastustaja -->
            <div>
                <label for="guest_team">Vastustaja:</label>
                <input type="text" id="guest_team" v-model="form.guest_team" placeholder="Vastustaja">
            </div>

            <!-- Vierasottelu -->
            <div>
                <label for="away_game">Vierasottelu:</label>
                <input type="checkbox" id="away_game" v-model="form.AwayCheckbox">
            </div>

            <!-- Paikka -->
            <div>
                <label for="location">Paikka:</label>
                <input type="text" id="location" v-model="form.game_location" placeholder="Paikka">
            </div>

            <!-- Päivämäärä -->
            <div>
                <label for="date">Pvm:</label>
                <input type="text" id="date" v-model="form.game_date" placeholder="Pvm">
            </div>

            <!-- Aloitusaika -->
            <div>
                <label for="start_time">Aloitusaika:</label>
                <input type="text" id="start_time" v-model="form.game_start_time" placeholder="Aloitusaika">
            </div>

            <!-- Kesto -->
            <div>
                <label for="duration">Kesto:</label>
                <input type="text" id="duration" v-model="form.game_duration" placeholder="Kesto (min)">
            </div>

            <!-- Ennakkoinfo -->
            <label for="public_info">Ennakkoinfo:</label>
            <div 
            id="public_info"
            contenteditable="true"
            v-html="form.game_public_info" 
            @input="updateContent"
            class="editable-content"
            >
            </div> 
           

            <button type="button" @click="submitForm">Päivitä</button>
        </form>
    </div>
</div>

<script>
export default {
  data() {
    return {
      form: {
        game_public_info: '' // HTML-sisältö
      }
    };
  },
  methods: {
    // Kun käyttäjä muokkaa sisältöä, päivitetään Vue data
    updateContent(event) {
      this.form.game_public_info = event.target.innerHTML;
    }
  }
};
</script>
<style>
.editable-content {
  border: 1px solid #ccc;
  padding: 10px;
  min-height: 100px;
  font-family: Arial, sans-serif;
  font-size: 14px;
  background-color: #f9f9f9;
}
</style>



`
});

// Mount the Vue app
app.mount('#schedule-app');