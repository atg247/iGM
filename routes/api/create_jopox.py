import logging

from flask import jsonify, request
from flask_login import login_required, current_user

from security import cipher_suite
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger

from . import api_bp

@api_bp.route('/create_jopox', methods=['POST'])
@login_required
def create_jopox():
    logging.debug('starting create_jopox')
    data = request.json
    game = data.get('game')
    level = data.get('level')
    logger.debug('game: %s', game)
    logger.debug('level: %s', level)

    username = current_user.jopox_username
    #decrypt password from database
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password
    scraper = JopoxScraper(current_user.id, username, password)

    logger.debug('starting create_jopox, calling ensure_logged_in and access_admin')
    logger.debug('data: %s', data)

    if scraper.access_admin():
        try: 
            game_data = {
                
                "LeagueDropdownList": "", #"15116" Treenipelit 24/25, "15449" U12 Sarja lohko, "15460" U12 Sarja lohko 3B
                "EventDropDownList": "",
                "HomeTeamTextBox": game.get("Home Team", ""),#muokattu S-kiekko Punainen muotoon Punainen - pitää keksiä joku logiikka
                "GuestTeamTextBox": game.get("Away Team", ""),
                "AwayCheckbox": "", #Tämä pitää setviä kuntoon jos tyhjä niin kotijoukkue on kotijoukkue ja jos "on" niin vierasjoukkue on kotijoukkue.
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
            scraper.add_game(game_data, game, level)
            return jsonify({"message": "Ottelu lisätty. Päivitä sivu nähdäksesi muutokset."}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
