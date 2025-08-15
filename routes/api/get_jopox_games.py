from flask import jsonify, current_app as app
from flask_login import login_required, current_user

from extensions import db
from models.user import User
from security import cipher_suite
from logging_config import logger
from helpers.jopox_scraper import JopoxScraper
from helpers.data_fetcher import hae_kalenteri

from . import api_bp


def json_error(message, status=500):
    return jsonify({"status": "error", "message": message}), status

@api_bp.route('/jopox_games')
@login_required
def get_jopox_games():
    logger.debug('starting api/jopox_games')
    user = db.session.get(User, current_user.id)

    # 1) Perustarkistukset
    if not user or not user.jopox_username:
        return json_error("Jopox‑käyttäjätunnus puuttuu", 400)
    if not user.jopox_password:
        return json_error("Jopox‑salasana puuttuu", 400)

    # 2) Salauksen purku – virheet kiinni
    try:
        decrypted_password = cipher_suite.decrypt(user.jopox_password).decode('utf-8')
    except Exception:
        app.logger.exception("Password decryption failed")
        return json_error("Tunnistetietojen käsittely epäonnistui", 500)

    # 3) Kalenterikuvausten haku – epäonnistuessa jatka tyhjällä
    descriptions = []
    if user.jopox_calendar_url:
        try:
            raw = hae_kalenteri(user.jopox_calendar_url)
            descriptions = raw or []
        except Exception:
            logger.warning("Calendar fetch failed, continuing without descriptions", exc_info=True)
            descriptions = []

    logger.debug(f'Found {len(descriptions)} descriptions for games')
    logger.debug(f'UIDs: {[d.get("Uid") for d in descriptions if isinstance(d, dict)]}')

    # 4) Jopox‑login
    scraper = JopoxScraper(user.id, user.jopox_username, decrypted_password)
    logger.debug('starting scraper with jopox_games, calling ensure_logged_in and access_admin')
    try:
        if not scraper.login():
            logger.warning('Admin access denied')
            return json_error("Jopox‑kirjautuminen epäonnistui", 403)
    except Exception:
        app.logger.exception("Login raised unexpectedly")
        return json_error("Jopox‑kirjautuminen epäonnistui", 502)

    # 5) Scrapea ja yhdistä kuvaukset turvallisesti
    try:
        jopox_games = scraper.scrape_jopox_games() or []
        # indeksointi turvallisesti .get:illä ettei KeyError kaada
        desc_by_uid = { (d or {}).get('Uid'): d for d in descriptions if isinstance(d, dict) and (d or {}).get('Uid') }
        for g in jopox_games:
            uid = (g or {}).get('uid')
            if uid and uid in desc_by_uid:
                g['Lisätiedot'] = desc_by_uid[uid].get('Lisätiedot')

        return jsonify({"status": "ok", "count": len(jopox_games), "data": jopox_games}), 200

    except Exception:
        app.logger.exception("Error fetching Jopox games")
        return json_error("Jopox‑tietojen haku epäonnistui", 502)