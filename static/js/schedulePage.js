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
                        console.log('All Games Structure:', this.allGames);
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
            console.log('toggleTeam called for team_id:', team_id); // Add this log
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
            this.filteredGames = this.allGames.filter(game => {
                const isMatch = this.selectedTeams.includes(String(game['Team ID']));
                return isMatch;
            });
        
            console.log('Filtered Games:', this.filteredGames);
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

                <!-- Games Table -->
                <h3 class="mt-4">Game Schedule</h3>
                <table v-if="filteredGames.length > 0" class="table">
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
                        <tr
                            v-for="game in filteredGames"
                            :key="game['Game ID']"
                            :style="getRowStyle(game)"
                        >
                            <td :style="{ backgroundColor: '#ffffff', color: '#000000' }">{{ game.Date }}</td>
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
