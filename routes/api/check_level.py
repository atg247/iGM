from flask import jsonify, request
from flask_login import current_user

from security import cipher_suite
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger

from . import api_bp

@api_bp.route('/check_level', methods=['GET'])
def check_level():
    
    logger.debug('starting check_level')
    level = request.args.get('level')  # Extract the uid from query parameters
    username = current_user.jopox_username
    #decrypt password from database
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password

    scraper = JopoxScraper(current_user.id, username, password)

    if scraper.access_admin():
        try:
            leagues = scraper.define_league(level)
            return leagues

        except Exception as e:
            return jsonify({"error": str(e)}), 500
