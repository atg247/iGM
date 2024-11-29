const app = Vue.createApp({
    data() {
        return {
            allGames: [], // All fetched games from the backend (already sorted)
            filteredGames: [], // Games to display in the table (filtered by team)
            managedTeams: [], // Managed teams
            followedTeams: [], // Followed teams
            selectedTeams: [], // Teams selected for inclusion in the table
            isLoading: true, // Show a loading indicator while fetching games
            showReasonPopup: false, // Controls popup visibility
            popupReason: "", // Stores the reason to display in the popup

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
                } else {
                    console.error('Unexpected Tulospalvelu response:', tulospalveluGames);
                }
        
                // Send data to backend for comparison
                return fetch('/api/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tulospalvelu_games: this.allGames, // Only unique games sent for comparison
                        jopox_games: jopoxGames.data, // Assuming Jopox data is in `.data`
                    }),
                });
            })
            .then(response => response.json())
            .then(comparisonResults => {
                // Update game cards with comparison results
                this.allGames = this.allGames.map(game => {
                    const match = comparisonResults.find(
                        result => result.game['Game ID'] === game['Game ID']
                    );
                    return {
                        ...game,
                        match_status: match?.match_status || 'red', // Default to red if no match
                        reason: match?.reason || 'No match found',
                    };
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
        
        filterGames() {
            if (this.selectedTeams.length === 0) {
                this.filteredGames = [];
                return;
            }
        
            // Filter games based on selected teams
            this.filteredGames = this.allGames.filter(game =>
                this.selectedTeams.includes(String(game['Team ID']))
            );
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
                       
                
        isTeamSelected(teamName) {
            // Check if a team is selected
            return this.selectedTeams.includes(teamName);
        },
        toggleReason(game) {
            if (game.reason) {
                this.popupReason = game.reason.replace(/\. /g, '<br>'); // Format the reason
                this.showReasonPopup = true; // Show modal
            }
        },
        closePopup() {
            this.showReasonPopup = false; // Hide modal
            this.popupReason = ""; // Clear the reason
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
    <div class="window-header">
        {{ getDayName(date) }} {{ games[0].Date }}
    </div>

    <!-- Game Info Cards -->
    <div class="game-cards">
        <div
            v-for="game in games"
            :key="game['Game ID'] + '-' + game['Team ID']"
            class="game-card"
            :style="getRowStyle(game)"
        >
            <div class="gameInfo1">
                <div class="topRow">
                    <p class="gameTeams">
                        {{ game['Home Team'] }} - {{ game['Away Team'] }}
                    </p>
                    <!-- Circle positioned to the right -->
                    <div class="status-box">
                        <span class="status-text">Jopox:</span>
                        <span
                            class="status-circle"
                            :class="{
                                'circle-green': game.match_status === 'green',
                                'circle-yellow': game.match_status === 'yellow',
                                'circle-red': game.match_status === 'red',
                            }"
                            @click="toggleReason(game)"
                        ></span>
                    </div>
                </div>
                <!-- Show reasons if clicked -->
                <div v-if="showReasonPopup" class="modal-overlay">
                    <div class="modal-window">
                        <span class="modal-close" @click="closePopup">&times;</span>
                        <h3>Match Details</h3>
                        <p v-html="popupReason"></p>
                    </div>
                </div>
            </div>

            <div class="bottomRow">
                <p class="gameTime"> Klo {{ game.Time || 'Aika ei saatavilla' }}</p>
                <p class="gameLocation">{{ game.Location || 'Paikka ei saatavilla' }}</p>
                <p class="gameStatgroup">{{ game['Level Name'] }}</p>
            </div>
        </div>
    </div>

</div>
`
});

// Mount the Vue app
app.mount('#schedule-app');