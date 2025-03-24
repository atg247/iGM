from flask import jsonify, current_app as app
from flask_login import login_required, current_user

from extensions import db
from models.user import User
from security import cipher_suite
from logging_config import logger
from helpers.jopox_scraper import JopoxScraper
from helpers.data_fetcher import hae_kalenteri

from . import api_bp

@api_bp.route('/jopox_games')
@login_required
def get_jopox_games():
    logger.debug('starting api/jopox_games')
    user = db.session.get(User, current_user.id)
    username = user.jopox_username
    #decrypt password from database
    encrypted_password = user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password
    j_team_id = user.jopox_team_id

    scraper = JopoxScraper(user.id, username, password)
    calendar_url = user.jopox_calendar_url
    descriptions = hae_kalenteri(calendar_url)
    logger.debug(f'Found {len(descriptions)} descriptions for games')
    logger.debug(f'UIDs: {[desc["Uid"] for desc in descriptions]}')
    logger.debug('starting scraper with jopox_games, calling ensure_logged_in and access_admin')
    if scraper.access_admin():
        try:
            jopox_games = scraper.scrape_jopox_games()
            for game in jopox_games:
                logger.debug(f'Processing game {game["uid"]}')
                matching_description = next((desc for desc in descriptions if desc['Uid'] == game['uid']), None)
                if matching_description:
                    logger.debug(f'Found matching description for game {game["uid"]}')
                    game['Lisätiedot'] = matching_description['Lisätiedot']
                
            return jsonify(jopox_games)
        except Exception as e:
            app.logger.error(f"Error fetching Jopox games: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
