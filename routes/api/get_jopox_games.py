import logging

from flask import jsonify
from flask_login import login_required, current_user

from extensions import db
from models.user import User
from app import app, cipher_suite

from helpers.jopox_scraper import JopoxScraper
from helpers.data_fetcher import hae_kalenteri

from . import api_bp

@api_bp.route('/api/jopox_games')
@login_required
def get_jopox_games():
    logging.debug('starting api/jopox_games')
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
    logging.debug('starting scraper with jopox_games, calling ensure_logged_in and access_admin')
    if scraper.access_admin():
        try:
            jopox_games = scraper.scrape_jopox_games()
            for game in jopox_games:
                matching_description = next((desc for desc in descriptions if desc['Uid'] == game['uid']), None)
                if matching_description:
                    game['Lisätiedot'] = matching_description['Lisätiedot']
            return jsonify(jopox_games)
        except Exception as e:
            app.logger.error(f"Error fetching Jopox games: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
