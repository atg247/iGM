import logging
import pandas as pd

from flask import request, jsonify

from helpers.game_fetcher import GameFetcher


from routes.api import api_bp


@api_bp.route('/gamefetcher/fetch_games', methods=['POST'])
def fetch_games():
    print('game fetcher started')
    dwl = 0
    season = request.form['season']
    stat_group_id = request.form['statgroup']
    distr_id = 0  
    GameDates = 3
    dog = '2024-10-12'
    selected_teams = request.form.getlist('teams')

    managed_games_df = pd.DataFrame()
    if not selected_teams:
        return jsonify({"error": "No teams selected. Please choose at least one team."})

    for team_id in selected_teams:
        fetcher = GameFetcher(dwl, season, stat_group_id, team_id, distr_id, GameDates, dog)
        error = fetcher.fetch_games()

        if error:
            return jsonify({"error": error})  # Return the error in JSON format

        games_df = fetcher.display_games()
        if not games_df.empty:
            managed_games_df = pd.concat([managed_games_df, games_df], ignore_index=True)

    if managed_games_df.empty:
        return jsonify({"error": "No games found for the selected teams."})

    # Convert the games DataFrame to a JSON format
    try:
        managed_games_data = managed_games_df.to_dict(orient='records')
        return jsonify(managed_games_data)
    except Exception as e:
        return jsonify({"error": f"Error processing games data: {str(e)}"})