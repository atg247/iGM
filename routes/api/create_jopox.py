import logging

from flask import jsonify, request
from flask_login import login_required, current_user
from fuzzywuzzy import fuzz

from security import cipher_suite
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger


from . import api_bp

@api_bp.route('/create_jopox', methods=['POST'])
@login_required
def create_jopox():
    logging.debug('starting create_jopox (bulk-compatible)')
    data = request.get_json(silent=True) or {}

    # Normalize to bulk format: { items: [ { game }, ... ] }
    items = data.get('items')
    if not isinstance(items, list):
        # Backward-compat: single payload { game, level }
        single_game = data.get('game')
        if single_game:
            items = [{ 'game': single_game }]
        else:
            items = []

    username = current_user.jopox_username
    # decrypt password from database
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password
    scraper = JopoxScraper(current_user.id, username, password)

    logger.debug('Request contains %d item(s)', len(items))

    results = []

    items = define_away_game(items)
    logger.debug('Example of items after define_away_game: %s', items[0])

    if not scraper.access_admin():
        return jsonify({ 'items': [{ 'status': 'error', 'error': 'admin_access_failed' }] }), 500

    for item in items:
        try:
            game = (item or {}).get('game') or {}
            if not game:
                results.append({ 'status': 'error', 'error': 'missing_game' })
                continue


            # Resolve league by TP level name found inside game
            level_name = game.get('Level Name', '') or ''
            league_id = scraper.define_league(level_name) if level_name else ''

            game_data = {
                "LeagueDropdownList": league_id or "",
                "EventDropDownList": "",
                "HomeTeamTextBox": game.get("Team Name", ""),
                "GuestTeamTextBox": game.get("away_team", ""),
                "AwayCheckbox": game.get("away_checkbox", ""),
                "GameLocationTextBox": game.get("Location", ""),
                "GameDateTextBox": game.get("Date", ""),
                "GameStartTimeTextBox": game.get("Time", ""),
                "GameDurationTextBox": game.get("GameDurationTextBox", "120"),
                "GameDeadlineTextBox": "",
                "GameMaxParticipatesTextBox": "",
                "FeedGameDropdown": "0",
                "GameNotificationTextBox": "",
                "SaveGameButton": "Tallenna"
            }

            add_result = scraper.add_game(game_data, game, league_id or "")

            # Heuristic success detection
            if isinstance(add_result, str) and 'error' not in add_result.lower():
                results.append({ 'status': 'ok', 'game_id': game.get('Game ID'), 'message': add_result })
            else:
                results.append({ 'status': 'error', 'game_id': game.get('Game ID'), 'error': add_result or 'unknown_error' })

        except Exception as e:
            logger.exception('Error while creating game')
            results.append({ 'status': 'error', 'error': str(e) })

    return jsonify({ 'items': results }), 200

def define_away_game(items):

    for item in items:
        game = item.get("game")
        
        t_home_team = game.get("Home Team", "") #Simulated home team 1
        t_away_team = game.get("Away Team", "") #S-Kiekko Sininen
        j_home_team = game.get("Team Name", "") #S-Kiekko Sininen
        
        home_team_score = fuzz.ratio(t_home_team, j_home_team)
        away_team_score = fuzz.ratio(t_away_team, j_home_team)
    


        if home_team_score < away_team_score:
            game["away_checkbox"] = "on"
            game["away_team"] = t_home_team

        else:
            game["away_checkbox"] = "off"
            game["away_team"] = t_away_team

    return items
