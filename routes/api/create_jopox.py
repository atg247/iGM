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
    logger.debug('starting create_jopox (bulk-compatible)')
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
    games_to_add = []

    items = define_away_game(items)

    if not scraper.access_admin():
        return jsonify({ 'items': [{ 'status': 'error', 'error': 'admin_access_failed' }] }), 500

    items = scraper.define_league(items)



    for item in items:
        game = item.get("game")
        if not game:
            results.append({ 'status': 'error', 'error': 'missing_game' })
            continue

        game_data = {
            "LeagueDropdownList": game.get("LeagueDropdownList", ""),
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

        games_to_add.append({
            "game": game,
            "game_data": game_data
        })
    
    try:
        results = scraper.add_game(games_to_add)

    except Exception as e:
        logger.exception('Error while creating game')
        results.append({ 'status': 'error', 'error': str(e) })

    return jsonify({ 'items': results }), 200

def define_away_game(items):

    for item in items:
        game = item.get("game")
        
        t_home_team = game.get("Home Team", "")
        t_away_team = game.get("Away Team", "")
        j_home_team = game.get("Team Name", "")

        home_team_score = fuzz.ratio(t_home_team, j_home_team)
        away_team_score = fuzz.ratio(t_away_team, j_home_team)
    


        if home_team_score < away_team_score:
            game["away_checkbox"] = "on"
            game["away_team"] = t_home_team

        else:
            game["away_checkbox"] = ""
            game["away_team"] = t_away_team

    return items
