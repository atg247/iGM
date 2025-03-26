from flask import jsonify
from flask_login import login_required, current_user
from flask import current_app as app

from extensions import db
from helpers.game_fetcher import GameFetcher
from logging_config import logger
from models.team import Team
from models.tgames import TGamesdb
from models.userteam import UserTeam

from . import api_bp

@api_bp.route('/schedules')
@login_required
def get_all_schedules():
    try:
        managed_teams = [
            {"team_name": team.team_name, "team_id": team.team_id, "season": team.season, "stat_group_id": team.statgroup, "type": 'manage'}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'manage').all()
        ]

        followed_teams = [
            {"team_name": team.team_name, "team_id": team.team_id, "season": team.season, "stat_group_id": team.statgroup, "type": 'follow'}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'follow').all()
        ]

        all_teams = managed_teams + followed_teams
        managed_games = []

        # Fetch games for each team
        for team in all_teams:
            logger.debug(f"Fetching games for {team['team_name']}")
            try:
                fetcher = GameFetcher(
                    dwl=0,  # Replace with actual value
                    season=team['season'],
                    stat_group_id=team['stat_group_id'],
                    team_id=team['team_id'],
                    distr_id=0,  # Replace with actual value if needed
                    GameDates=3,  # Replace with actual value if needed
                    dog='2024-10-12'  # Replace with actual date logic if needed
                )
                error = fetcher.fetch_games()

                if error:
                    app.logger.error(f"Error fetching games for {team['team_name']}: {error}")
                    continue  # Skip this team if there's an error

                # Format the games using display_games helper
                games_df = fetcher.display_games()
                if not games_df.empty:
                    games_df['Team Name'] = team['team_name']
                    games_df['Type'] = team['type']  # Manage or Follow

                    # Add formatted and sortable dates
                    games_df['SortableDate'] = games_df['Date']
                    games_df['Date'] = games_df['Date'].dt.strftime('%d.%m.%Y')  # Format for display
                    managed_games.extend(games_df.to_dict(orient='records'))

            except Exception as e:
                app.logger.error(f"Error fetching games for {team['team_name']}: {str(e)}")
                continue  # Skip to the next team if error occurs during fetch

        # Sort all games by sortable date and time
        managed_games = sorted(managed_games, key=lambda game: (game['SortableDate'], game['Time']))
        app.logger.debug(f"Managed games fetched: {len(managed_games)} games")
        
        # Store the games in the database if not already there based on game id
        updated_games = []  # List of updated games
        added_games = []  # List of added games

        for game in managed_games:
            try:
                #app.logger.debug(f"Checking if game {game['Game ID']} already exists")
                # Check if the game already exists
                existing_game = TGamesdb.query.filter_by(game_id=game['Game ID']).first()

                if existing_game:
                    # Compare existing game and new game
                    changes = {}

                    if existing_game.date != game['Date']:
                        changes['date'] = {'old': existing_game.date, 'new': game['Date']}
                        existing_game.date = game['Date']

                    # Check if the time has changed
                    if existing_game.time != game['Time']:
                        changes['time'] = {'old': existing_game.time, 'new': game['Time']}
                        existing_game.time = game['Time']

                    # Check if the location has changed
                    if existing_game.location != game['Location']:
                        changes['location'] = {'old': existing_game.location, 'new': game['Location']}
                        existing_game.location = game['Location']


                    # If there are any changes, add this game to the updated games list
                    if changes:
                        updated_games.append({
                            'game_id': game['Game ID'],
                            'changes': changes
                        })
                else:
                    # If the game doesn't exist, add it as a new game
                    new_game = TGamesdb(
                        game_id=game['Game ID'],
                        team_id=game['Team ID'],
                        date=game['Date'],
                        time=game['Time'],
                        home_team=game['Home Team'],
                        away_team=game['Away Team'],
                        home_goals=game['Home Goals'],
                        away_goals=game['Away Goals'],
                        location=game['Location'],
                        level_name=game['Level Name'],
                        stat_group_name=game['Stat Group Name'],
                        small_area_game=game['Small Area Game'],
                        team_name=game['Team Name'],
                        type=game['Type'],
                        sortable_date=game['SortableDate']
                    )
                    if new_game:
                        added_games.append({
                            'game date': new_game.date,
                            'game id': new_game.game_id
                        })

                    db.session.add(new_game)
            
            except Exception as e:
                app.logger.error(f"Error processing game {game['Game ID']}: {str(e)}")
        print("Example of managed games: ", managed_games[0])

        try:
            db.session.commit()
            app.logger.debug("Commit successful.")
        except Exception as e:
            app.logger.error(f"Error committing changes: {str(e)}")
            db.session.rollback()

        if updated_games:
            app.logger.debug(f"Updated games: {updated_games}")
        if added_games:
            app.logger.debug(f"Added games: {added_games}")
        
        for i in range(4):
            #Create one simulated game and include it in the DataFrame
            simulated_game = {
                
                "Game ID": f"202020202{i}",
                "SortableDate": f"Thu, 0{i+1} Jul 2025 00:00:00 GMT",
                "Date": f"0{i+1}.07.2025",
                "Team ID": "1368626270",
                "Team Name": "S-Kiekko Sininen",
                "Time": "12:00",
                "Home Team": "S-Kiekko Sininen",
                "Away Team": f"Simulated away team {i}",
                "Home Goals": "",
                "Away Goals": "",
                "Location": "Simulated location",
                "Level Name": "U13 A",
                "Stat Group Name":"TESTISARJA",
                "Small Area Game": "0",
                "Type": "manage"
            }
            managed_games.append(simulated_game)



        return jsonify({
            "managed_games": managed_games,
            "updated_games": updated_games,
            "message": f"Games processed successfully. Added games: {len(added_games)}, Updated games: {len(updated_games)}"
        }), 200

    except Exception as e:
        db.session.rollback()  # Rollback in case of any error in the outer block
        app.logger.error(f"Error fetching schedules: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

        # Palautetaan muutokset frontendille