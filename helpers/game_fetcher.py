import requests
import pandas as pd

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
        url = "https://tulospalvelu.leijonat.fi/helpers/getGames.php"
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
            self.games = response.json()  # Assuming the response is a list of games directly

            return None  # No error
        except requests.RequestException as e:
            return f"Error fetching games: {str(e)}"

    def display_games(self):
        if not self.games:
            return pd.DataFrame()  # Return an empty DataFrame if no games are found
    
        games_info = []
        
        for level_data in self.games:
            matches = level_data.get('Games', [])
            if not matches:
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
                    'Level Name': game.get('LevelName', 'N/A'),
                    'Stat Group Name': game.get('StatGroupName', 'N/A'),
                    'Small Area Game': game.get('SmallAreaGame', 'N/A')
                }
                games_info.append(game_info)

        games_df = pd.DataFrame(games_info)
        games_df['Date'] = pd.to_datetime(games_df['Date'], format='%d.%m.%Y', errors='coerce', dayfirst=True)
        
        return games_df
