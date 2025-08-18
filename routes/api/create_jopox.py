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


    away_checkbox = define_away_game(game)
    away_checkbox_value = away_checkbox.get("away_checkbox")
    away_team = away_checkbox.get("away_team")


    if scraper.access_admin():
        try: 
            game_data = {
                
                "LeagueDropdownList": "", #"15116" Treenipelit 24/25, "15449" U12 Sarja lohko, "15460" U12 Sarja lohko 3B
                "EventDropDownList": "",
                "HomeTeamTextBox": game.get("Team Name", ""),#muokattu S-kiekko Punainen muotoon Punainen - pitää keksiä joku logiikka
                "GuestTeamTextBox": away_team,
                "AwayCheckbox": away_checkbox_value, #Tämä pitää setviä kuntoon jos tyhjä niin kotijoukkue on kotijoukkue ja jos "on" niin vierasjoukkue on kotijoukkue.
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

def define_away_game(game):
    t_home_team = game.get("Home Team", "") #Simulated home team 1
    t_away_team = game.get("Away Team", "") #S-Kiekko Sininen
    j_home_team = game.get("Team Name", "") #S-Kiekko Sininen
    
    home_team_score = fuzz.ratio(t_home_team, j_home_team)
    away_team_score = fuzz.ratio(t_away_team, j_home_team)
    


    if home_team_score < away_team_score:
        return {
            "away_checkbox": "on",
            "away_team": t_home_team
        }
    else:
        return {
            "away_checkbox": "off",
            "away_team": t_away_team
            }
