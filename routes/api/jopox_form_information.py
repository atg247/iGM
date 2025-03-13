import logging

from flask import jsonify, request
from flask_login import current_user

from app import cipher_suite
from helpers.jopox_scraper import JopoxScraper

from . import api_bp

@api_bp.route('/api/jopox_form_information')
def jopox_form_information():
    
    logging.debug('starting jopox_form_information')
    j_game_id = request.args.get('uid')  # Extract the uid from query parameters
    username = current_user.jopox_username
    #decrypt password from database
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password

    scraper = JopoxScraper(current_user.id, username, password)
    logging.debug('starting scraper with jopox_form_information, calling access_admin')
    if scraper.access_admin():
        try:
            jopox_form_information = scraper.j_game_details(j_game_id)
            return jopox_form_information

        except Exception as e:
            return jsonify({"error": str(e)}), 500
