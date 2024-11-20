const app = Vue.createApp({
    data() {
        return {
            allGames: [], // All fetched games from the backend (already sorted)
            filteredGames: [], // Games to display in the table (filtered by team)
            managedTeams: [], // Managed teams
            followedTeams: [], // Followed teams
            selectedTeams: [], // Teams selected for inclusion in the table
            isLoading: true, // Show a loading indicator while fetching games
        };
    },
    methods: {
        fetchGames() {
            // Fetch all schedules from the backend
            this.isLoading = true;
            fetch('/api/schedules')
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        this.allGames = data; // Dates are already formatted and sorted by the backend
                        this.filterGames(); // Filter to default managed teams
                    } else {
                        console.error('Unexpected response:', data);
                    }
                })
                .catch(error => {
                    console.error('Error fetching games:', error);
                })
                .finally(() => {
                    this.isLoading = false;
                });
        },
        fetchTeams() {
            // Fetch all teams (managed and followed) from the backend
            fetch('/api/teams')
                .then(response => response.json())
                .then(data => {
                    this.managedTeams = data.managed_teams;
                    this.followedTeams = data.followed_teams;
                    // Select managed teams by default
                    this.selectedTeams = data.managed_teams.map(team => team.team_name);
                    this.filterGames(); // Immediately filter games based on managed teams
                    
                    // Log data after assignment
                    console.log("Managed Teams:", this.managedTeams);
                    console.log("Followed Teams:", this.followedTeams);
                })
                .catch(error => {
                    console.error('Error fetching teams:', error);
                });
        },
        

        toggleTeam(teamName) {
            // Add or remove team from selectedTeams
            if (this.selectedTeams.includes(teamName)) {
                this.selectedTeams = this.selectedTeams.filter(name => name !== teamName);
            } else {
                this.selectedTeams.push(teamName);
            }
            this.filterGames(); // Update the table with new selection
        },
        filterGames() {
            // If no teams are selected, clear the filteredGames array
            if (this.selectedTeams.length === 0) {
                this.filteredGames = [];
                return;
            }

            // Otherwise, filter games by selected teams
            this.filteredGames = this.allGames.filter(game =>
                this.selectedTeams.includes(game['Team Name'])
            );
        },
        getButtonColor(teamName) {
            // Map Finnish color words to lighter versions of colors
            const colorMap = {
                musta: '#282828', // Light Gray
                punainen: '#ff5151', // Light Red
                sininen: '#2c778f', // Light Blue
                keltainen: '#ffff08', // Light Yellow
                valkoinen: '#cccccc', // White
                vihreä: '#137f13', // Light Green
            };
        
            // Check for color in team name
            const lowerCaseName = teamName.toLowerCase();
            for (const [key, value] of Object.entries(colorMap)) {
                if (lowerCaseName.includes(key)) {
                    return value; // Return the light color if found
                }
            }
        
            // Default light gray if no keyword found
            return '#E0E0E0';
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
        
                
        isTeamSelected(teamName) {
            // Check if a team is selected
            return this.selectedTeams.includes(teamName);
        },
    },
    mounted() {
        this.fetchTeams(); // Fetch teams first
        this.fetchGames(); // Then fetch all games
    },

    template: `
        <div class="container my-4">
            <div>
                <h1>Valittujen joukkueiden ohjelma Tulospalvelusta.</h1>
                <p> Tässä näkymässä esitetään oletuksena hallinnoimiesi joukkueiden otteluohjelma.</p>
                <p> Valitse näytettävät joukkueet painikkeista.</p>
                <br>
            </div>

            
            <!-- Sticky Team Selector -->
            <div class="sticky-team-selector">              
                <!-- Managed Teams -->
                <h1>Hallinnoimasi joukkueet</h1>
                <div class="btn-group">
                    <button
                        v-for="team in managedTeams"
                        :key="team.team_id"
                        @click="toggleTeam(team.team_name)"
                        :style="{
                            backgroundColor: getButtonColor(team.team_name),
                            color: getTextColor(getButtonColor(team.team_name), isTeamSelected(team.team_name)),
                            }"
                        :class="['btn', isTeamSelected(team.team_name) ? 'selected-team' : 'unselected-team']"
                    >
                        {{ team.team_name }}<br>{{ team.stat_group}}
                    </button>





                </div>
                
                <!-- Followed Teams -->
                <h1>Seuraamasi joukkueet</h1>
                <div class="btn-group">
                    <button
                        v-for="team in followedTeams"
                        @click="toggleTeam(team.team_name)"
                        :style="{
                            backgroundColor: getButtonColor(team.team_name),
                            color: getTextColor(getButtonColor(team.team_name), isTeamSelected(team.team_name)),
                            }"
                        :class="['btn', isTeamSelected(team.team_name) ? 'selected-team' : 'unselected-team']"                    >
                        {{ team.team_name }}<br>{{ team.stat_group }}
                    </button>
                </div>
            </div>



            <!-- Loading Indicator -->
            <div v-if="isLoading" class="my-4">
                <p>Loading games...</p>
            </div>

                <!-- Games Table -->
                <h3 class="mt-4">Game Schedule</h3>
                <table v-if="filteredGames.length > 0" class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Home Team</th>
                            <th>Away Team</th>
                            <th>Location</th>
                            <th>Level</th>
                            <th>Team</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="game in filteredGames" :key="game['Game ID']">
                            <td>{{ game.Date }}</td>
                            <td>{{ game.Time }}</td>
                            <td>{{ game['Home Team'] }}</td>
                            <td>{{ game['Away Team'] }}</td>
                            <td>{{ game.Location }}</td>
                            <td>{{ game['Level Name'] }}</td>
                            <td>{{ game['Team Name'] }}</td>
                        </tr>
                    </tbody>
                </table>
                <p v-else>No games to display. Please select a team.</p>
            </div>
                `,
});

// Mount the Vue app
app.mount('#schedule-app');
