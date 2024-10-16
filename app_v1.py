import os
from flask import Flask, render_template, request, jsonify # type: ignore
import requests
import pandas as pd

# Initialize the Flask app
app = Flask(__name__)

# Fetch levels for a given season.
def get_levels(season):
    url = "https://tulospalvelu.leijonat.fi/helpers/getLevels.php"
    payload = {'season': season}
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

# Fetch statistic groups based on a specific level ID.
def get_stat_groups(season, level_id, district_id=0):
    url = "https://tulospalvelu.leijonat.fi/serie/helpers/getStatGroups.php"
    payload = {
        'season': season,
        'levelid': level_id,
        'districtid': district_id
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

# Fetch teams based on a selected statistic group ID.
def get_teams(season, stat_group_id):
    url = "https://tulospalvelu.leijonat.fi/serie/helpers/getStatGroup.php"
    payload = {'season': season, 'stgid': stat_group_id}
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

# GameFetcher class for fetching game data.
class GameFetcher:
    def __init__(self, dwl, season, stat_group_id, team_id, distr_id, GameDates, dog):
        self.dwl = dwl
        self.season = season
        self.stat_group_id = stat_group_id
        self.team_id = team_id
        self.distr_id = distr_id
        self.GameDates = GameDates
        self.dog = dog
        self.games = []

    def fetch_games(self):
        url = "https://tulospalvelu.leijonat.fi/helpers/getGames.php"  # Replace with the actual URL for fetching games
        payload = {
            'dwl': self.dwl,
            'season': self.season,
            'stgid': self.stat_group_id,
            'teamid': self.team_id,
            'districtid': self.distr_id,
            'gamedays': self.GameDates,
            'dog': self.dog            
        }
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            # Assuming the response is a list of games directly
            self.games = response.json()  # No .get() here since we're expecting a list
            return None  # No error
        except requests.RequestException as e:
            return f"Error fetching games: {str(e)}"

    def display_games(self):
        if not self.games:
            return pd.DataFrame()  # Return an empty DataFrame if no games are found
    
        games_info = []
        
        for level_data in self.games:
            matches = level_data.get('Games', [])
            
            if not matches:  # Check if there are any games in this level
                continue
                
            for game in matches:
                game_info = {
                    'Team ID': self.team_id,
                    'Game ID': game.get('GameID', 'N/A'),
                    'Date': game.get('GameDate', 'N/A'),
                    'Time': game.get('GameTime', 'N/A'),
                    'Home Team': game.get('HomeTeamAbbrv', 'N/A'),
                    'Away Team': game.get('AwayTeamAbbrv', 'N/A'),
                    'Home Goals': game.get('HomeGoals', 'N/A'),
                    'Away Goals': game.get('AwayGoals', 'N/A'),
                    'Location': game.get('RinkName', 'N/A'),
                    'Level Name': level_data.get('LevelName', 'N/A'),
                }
                games_info.append(game_info)

        games_df = pd.DataFrame(games_info)
        # Ensure Date column is in datetime format to allow proper sorting
        games_df['Date'] = pd.to_datetime(games_df['Date'], format='%d.%m.%Y', errors='coerce', dayfirst=True)
        return games_df

# Home page route.
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch levels for a given season.
@app.route('/get_levels/<season>')
def get_levels_endpoint(season):
    levels = get_levels(season)
    return jsonify(levels)

# Route to fetch statistic groups for a given level.
@app.route('/get_statgroups/<season>/<level_id>/<district_id>')
def get_statgroups(season, level_id, district_id=0):
    stat_groups = get_stat_groups(season, level_id, district_id)
    return jsonify(stat_groups)

# Route to fetch teams for a given statistic group.
@app.route('/get_teams/<season>/<stat_group_id>')
def get_teams_endpoint(season, stat_group_id):
    teams = get_teams(season, stat_group_id) 
    return jsonify(teams)

# Route to handle form data submission to fetch games.
@app.route('/fetch_games', methods=['POST'])
def fetch_games():
    dwl = 0
    season = request.form['season']
    stat_group_id = request.form['statgroup']
    distr_id = 0  
    GameDates = 3
    dog = '2024-10-12'
    selected_teams = request.form.getlist('teams')

    all_games_df = pd.DataFrame()

    if not selected_teams:
        return jsonify({"error": "No teams selected. Please choose at least one team."})

    for team_id in selected_teams:
        fetcher = GameFetcher(dwl, season, stat_group_id, team_id, distr_id, GameDates, dog)
        error = fetcher.fetch_games()

        if error:
            return jsonify({"error": error})  # Return the error in JSON format

        games_df = fetcher.display_games()
        if not games_df.empty:
            all_games_df = pd.concat([all_games_df, games_df], ignore_index=True)

    if all_games_df.empty:
        return jsonify({"error": "No games found for the selected teams."})

    # Convert the games DataFrame to a JSON format
    try:
        all_games_data = all_games_df.to_dict(orient='records')
        return jsonify(all_games_data)
    except Exception as e:
        return jsonify({"error": f"Error processing games data: {str(e)}"})

# Route to forward selected games.
@app.route('/send_selected_games', methods=['POST'])
def send_selected_games():
    try:
        # Get JSON data from the request body
        data = request.get_json()
        
        # Check if 'selected_games' is in the received data
        if not data or 'selected_games' not in data:
            return jsonify({"error": "No games selected. Please choose at least one game."}), 400

        selected_games = data['selected_games']

        # Print the selected game details to the console (for debugging/demo purposes)
        selected_game_details = []
        for game in selected_games:
            print(f"Selected game details: {game}")
            selected_game_details.append(game)

        # Send success response
        return jsonify({"message": "Tämä toiminto ei ikävä kyllä ole vielä käytössä.", "games": selected_game_details}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


#'Game ID': game.get('GameID', 'N/A'),
 #                   'Date': game.get('GameDate', 'N/A'),
  #                  'Time': game.get('GameTime', 'N/A'),
   #                 'Home Team': game.get('HomeTeamAbbrv', 'N/A'),
    #                'Away Team': game.get('AwayTeamAbbrv', 'N/A'),
     #               'Home Goals': game.get('HomeGoals', 'N/A'),
      #              'Away Goals': game.get('AwayGoals', 'N/A'),
       #             'Location': game.get('RinkName', 'N/A'),
        #            'Level Name': level_data.get('LevelName', 'N/A'),


    
    print(selected_game_details)

    return jsonify({"message": "Selected games forwarded successfully.", "games": selected_game_details})

# Start the Flask app in debug mode.
if __name__ == '__main__':
    # Bind to the $PORT if defined, otherwise use 5000 for local development.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
