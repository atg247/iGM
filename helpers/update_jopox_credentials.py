from extensions import session, db
from models.user import db, User
from flask_login import current_user
from security import cipher_suite
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger


def update_jopox_credentials():
    logger.debug('starting update_jopox_credentials')
    #hae käyttäjän tiedot tietokannasta
    username = current_user.jopox_username
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password
    scraper = JopoxScraper(current_user.id, username, password)
    credentials = scraper.login_for_credentials()

    logger.info(f"Credentials: {credentials}")
    #päivitä credentials tietokantaan
    current_user.jopox_team_id = credentials['jopox_team_id']
    current_user.jopox_calendar_url = credentials['calendar_url']
    db.session.commit()

    return True


