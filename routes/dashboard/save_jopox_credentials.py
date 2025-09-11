from flask import jsonify, request
from flask_login import login_required, current_user

from models.user import User
from extensions import db
from security import cipher_suite
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger

from . import dashboard_bp

@dashboard_bp.route('/dashboard/save_jopox_credentials', methods=['POST'])
@login_required
def save_jopox_credentials():
    data = request.get_json()
    login_url = data['jopoxLoginUrl']
    username = data['username']
    password = data['password']
    
    # Salataan salasana
    encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
    # Tallennetaan käyttäjän tiedot tietokantaan
    user = db.session.get(User, current_user.id)  # Oletetaan, että käyttäjän tiedot haetaan sessiosta
    user.jopox_login_url = login_url
    user.jopox_username = username
    user.jopox_password = encrypted_password

    #kirjaudutaan jopoxiin ja haetaan joukkuetiedot
    scraper = JopoxScraper(user.id, username, password)
    jopox_credentials = scraper.login_for_credentials()

    if jopox_credentials == 401:
        logger.error("Failed to retrieve jopox credentials")
        return jsonify({'error': 'Failed to retrieve jopox credentials. Invalid username or password.'}), 401

    logger.info("jopox credentials received")

    # Tallennetaan joukkueen tiedot tietokantaan
    user.jopox_team_name = jopox_credentials['jopox_team_name']
    user.jopox_team_id = jopox_credentials['jopox_team_id']
    user.jopox_calendar_url = jopox_credentials['calendar_url']
    
    db.session.commit()

    return jsonify({'message': 'Jopox credentials saved successfully.'}), 200
