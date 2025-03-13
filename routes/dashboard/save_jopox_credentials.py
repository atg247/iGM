from flask import jsonify, request
from flask_login import login_required, current_user
from models.user import User
from extensions import db
from app import app
from app import cipher_suite
from helpers.jopox_scraper import JopoxScraper
import logging

@app.route('/dashboard/save_jopox_credentials', methods=['POST'])
@login_required
def save_jopox_credentials():
    data = request.get_json()
    login_url = data['jopoxLoginUrl']
    username = data['username']
    password = data['password']
    print(f"Received Jopox credentials: {username}, {password}, {login_url}")
    
    # Salataan salasana
    encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
    print(f"Encrypted password: {encrypted_password}")
    # Tallennetaan käyttäjän tiedot tietokantaan
    user = db.session.get(User, current_user.id)  # Oletetaan, että käyttäjän tiedot haetaan sessiosta
    user.jopox_login_url = login_url
    user.jopox_username = username
    user.jopox_password = encrypted_password

    print(f"password saved: {user.jopox_password}")
    print(f"username saved: {user.jopox_username}")
    print(f"login_url saved: {user.jopox_login_url}")
    #kirjaudutaan jopoxiin ja haetaan joukkuetiedot
    scraper = JopoxScraper(user.id, username, password)
    jopox_credentials = scraper.login_for_credentials()
    logging.info(f"jopox credentials received: {jopox_credentials}")

    # Tallennetaan joukkueen tiedot tietokantaan
    user.jopox_team_name = jopox_credentials['jopox_team_name']
    user.jopox_team_id = jopox_credentials['jopox_team_id']
    user.jopox_calendar_url = jopox_credentials['calendar_url']
    
    db.session.commit()

    print(f"Jopox credentials saved successfully for user {user.username}.")
    return jsonify({'message': 'Jopox credentials saved successfully.'}), 200
