import logging

from flask import jsonify, request
from flask_login import login_required, current_user

from security import cipher_suite
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger
from extensions import db

from . import api_bp

@api_bp.route('/update_jopox', methods=['POST'])
@login_required
def update_jopox():
    logger.debug('starting update_jopox')
    data = request.json
    game = data.get('game')
    best_match = data.get('best_match')
    form = data.get('form')
    uid = best_match.get('uid')
    logger.debug('NEW FORM: %s', form)
    away = form.get('AwayCheckbox', None)
    logger.debug('AWAYBOX: %s', away)

    username = current_user.jopox_username
    #decrypt password from database
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password

    scraper = JopoxScraper(current_user.id, username, password)

    if scraper.access_admin():
        try:
            game_data = {
                "SeasonId": "547",
                "SubSiteId": "8787",
                "LeagueDropdownList": form.get("league_selected", {}).get("value", ""), 
                "EventDropDownList": form.get("event_selected", {}).get("value", ""),
                "HomeTeamTextBox": form.get("HomeTeamTextbox", ""),#muokattu S-kiekko Punainen muotoon Punainen - pitää keksiä joku logiikka
                "GuestTeamTextBox": form.get("guest_team", ""),
                "AwayCheckbox": form["AwayCheckbox"], #Tämä pitää setviä kuntoon jos tyhjä niin kotijoukkue on kotijoukkue ja jos "on" niin vierasjoukkue on kotijoukkue.
                "GameLocationTextBox": form.get("game_location", ""),
                "GameDateTextBox": form.get("game_date", ""),
                "GameStartTimeTextBox": form.get("game_start_time", ""),
                "GameDurationTextBox": form.get("game_duration", "120"),
                "GameDeadlineTextBox": "",
                "GameMaxParticipatesTextBox": "",
                "GamePublicInfoTextBox": f"""{form.get("game_public_info")}""",
                "FeedGameDropdown": "0",
                "GameInfoTextBox": f"""{form.get("game_public_info")}""",
                "GameNotificationTextBox": "",
                "SaveGameButton": "Tallenna"
                }
            
            logger.info(f"STARTING scraper to modify game: {uid}")
            logger.info(f"Scraping with data: {game_data}")
            scraper.modify_game(game_data, uid)
            
            if scraper.modify_game:
                current_user.edited_jopox_entries = (current_user.edited_jopox_entries or 0) + 1
                db.session.commit()


            user = current_user
            
            return jsonify({"message": "Pelin tiedot muokattu"}), 200
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
