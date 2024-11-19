// static/js/schedulePage.js

// Create the Vue application
const app = Vue.createApp({
    data() {
        return {
            managedTeams: [], // List of managed teams
            followedTeams: [], // List of followed teams
            selectedTeam: null, // Currently selected team
            schedules: [], // Game schedules for the selected team
            isLoadingTeams: false, // Loading state for teams
            isLoadingSchedules: false, // Loading state for schedules
        };
    },
    methods: {
        // Fetch managed and followed teams from the backend
        fetchTeams() {
            this.isLoadingTeams = true;
            fetch('/api/teams')
                .then(response => response.json())
                .then(data => {
                    this.managedTeams = data.managed_teams || [];
                    this.followedTeams = data.followed_teams || [];
                    this.isLoadingTeams = false;
                })
                .catch(error => {
                    console.error('Error fetching teams:', error);
                    this.isLoadingTeams = false;
                });
        },
        // Fetch schedules for the selected team
        fetchSchedules(team) {
            this.isLoadingSchedules = true;
            fetch(`/api/schedules?team=${encodeURIComponent(team.team_name)}`)
                .then(response => response.json())
                .then(data => {
                    this.schedules = data || [];
                    this.isLoadingSchedules = false;
                })
                .catch(error => {
                    console.error('Error fetching schedules:', error);
                    this.isLoadingSchedules = false;
                });
        },
        // Handle team selection
        selectTeam(team) {
            this.selectedTeam = team;
            this.fetchSchedules(team);
        }
    },
    mounted() {
        this.fetchTeams(); // Fetch teams when the app is mounted
    },
    template: `
        <div class="container my-4">
            <h2>Otteluohjelmien selaus</h2>

            <!-- Loading indicator for teams -->
            <div v-if="isLoadingTeams" class="my-4">
                <p>Loading teams...</p>
            </div>

            <!-- Display managed teams -->
            <div v-else>
                <h1>Hallinnoimasi joukkueet</h1>
                <div class="btn-group">
                    <button
                        v-for="team in managedTeams"
                        :key="team.team_id"
                        @click="selectTeam(team)"
                        :class="['btn', selectedTeam?.team_id === team.team_id ? 'btn-primary' : 'btn-secondary']"
                    >
                        {{ team.team_name }}
                    </button>
                </div>

                <!-- Display followed teams -->
                <h1 class="mt-4">Seuratut joukkueet</h1>
                <div class="btn-group">
                    <button
                        v-for="team in followedTeams"
                        :key="team.team_id"
                        @click="selectTeam(team)"
                        :class="['btn', selectedTeam?.team_id === team.team_id ? 'btn-primary' : 'btn-secondary']"
                    >
                        {{ team.team_name }}
                    </button>
                </div>
            </div>

            <!-- Loading indicator for schedules -->
            <div v-if="isLoadingSchedules" class="my-4">
                <p>Loading schedules for {{ selectedTeam?.team_name }}...</p>
            </div>

            <!-- Display schedules -->
            <div v-else-if="selectedTeam" class="my-4">
                <h5>Schedules for {{ selectedTeam.team_name }}</h5>
                <table id="gamesTable" class="table">
                    <thead>
                        <tr>
                            <th>Pvm</th>
                            <th>Klo</th>
                            <th>Koti</th>
                            <th>Vieras</th>
                            <th>Halli</th>
                            <th>Kotijoukkue</th>
                            <th>Sarjataso</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="game in schedules" :key="game.id">
                            <td>{{ game.date }}</td>
                            <td>{{ game.time }}</td>
                            <td>{{ game.location }}</td>
                            <td>{{ game.opponent }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `,
});

// Mount the Vue app to the DOM
app.mount('#schedule-app');
