import logging

from flask import jsonify, request
from flask_login import login_required, current_user
from fuzzywuzzy import fuzz

from models import user
from models.tgames import TGamesdb
from extensions import db
from security import cipher_suite
from helpers.game_templates import GAME_INFO_MESSAGE, render_public_info
from helpers.jopox_scraper import JopoxScraper
from logging_config import logger


from . import api_bp

@api_bp.route('/create_jopox', methods=['POST'])
@login_required
def create_jopox():
    logger.debug('starting create_jopox (bulk-compatible)')
    data = request.get_json(silent=True) or {}

    # Normalize to bulk format: { items: [ { game }, ... ] }
    items = data.get('items')
    if not isinstance(items, list):
        # Backward-compat: single payload { game, level }
        single_game = data.get('game')
        if single_game:
            items = [{ 'game': single_game }]
        else:
            items = []

    username = current_user.jopox_username
    # decrypt password from database
    encrypted_password = current_user.jopox_password
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode('utf-8')
    password = decrypted_password
    scraper = JopoxScraper(current_user.id, username, password)

    logger.debug('Request contains %d item(s)', len(items))

    results = []
    games_to_add = []

    items = define_away_game(items)

    if not scraper.access_admin():
        return jsonify({ 'items': [{ 'status': 'error', 'error': 'admin_access_failed' }] }), 500

    items = scraper.define_league(items)



    for item in items:
        game = item.get("game")
        if not game:
            results.append({ 'status': 'error', 'error': 'missing_game' })
            continue

        game_data = {
            "LeagueDropdownList": game.get("LeagueDropdownList", ""),
            "EventDropDownList": "",
            "HomeTeamTextBox": game.get("Team Name", ""),
            "GuestTeamTextBox": game.get("away_team", ""),
            "AwayCheckbox": game.get("away_checkbox", ""),
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

        # Ennakkoinfo renderöidään täällä, ei scraperissa. Templaattiargumentti jää
        # toistaiseksi pois, jolloin käytetään oletusta - käyttäjän oma templaatti
        # kytketään tähän kun asetukset on toteutettu.
        game_data["GamePublicInfoTextBox"] = render_public_info(game, game_data)
        # Viestikenttä tyhjäksi: se lähtee osallistujille notifikaationa, eikä ottelun
        # luonnin kuulu ilmoittaa kenellekään.
        game_data["GameInfoTextBox"] = GAME_INFO_MESSAGE

        games_to_add.append({
            "game": game,
            "game_data": game_data
        })

    try:
        results, known_uids_before_batch = scraper.add_game(games_to_add)

        for r in results:
            if r.get('status') != 'ok' or not r.get('jopox_uid'):
                continue

            row = TGamesdb.query.filter_by(game_id=r['game_id']).first()
            if not row:
                continue

            if row.jopox_uid and row.jopox_uid != r['jopox_uid']:
                # known_uids_before_batch is None when the initial scrape failed - treat that the
                # same as "still exists" (safe default) rather than risk overwriting a valid link.
                if known_uids_before_batch is None or row.jopox_uid in known_uids_before_batch:
                    logger.info(
                        "create_jopox: game_id %s already linked to jopox_uid %s (still valid or "
                        "unconfirmed) - not replacing it with new jopox_uid %s",
                        row.game_id, row.jopox_uid, r['jopox_uid']
                    )
                    continue
                # Old uid no longer existed right before this creation - Jopox never reissues a
                # deleted uid, so the old event was hard-deleted and it's safe to repoint the link.
                logger.info(
                    "create_jopox: updating stale jopox_uid %s -> %s for game_id %s",
                    row.jopox_uid, r['jopox_uid'], row.game_id
                )

            conflict = TGamesdb.query.filter(
                TGamesdb.jopox_uid == r['jopox_uid'],
                TGamesdb.team_id == row.team_id,
                TGamesdb.game_id != row.game_id,
            ).first()
            if conflict:
                logger.warning(
                    "Refusing to link jopox_uid %s to game_id %s: already linked to game_id %s",
                    r['jopox_uid'], row.game_id, conflict.game_id
                )
                continue

            row.jopox_uid = r['jopox_uid']

        created_count = sum(1 for r in results if r.get('status') == 'ok')
        if created_count:
            current_user.created_jopox_entries = (current_user.created_jopox_entries or 0) + created_count
            db.session.commit()

    except Exception as e:
        logger.exception('Error while creating game')
        results.append({ 'status': 'error', 'error': str(e) })

    return jsonify({ 'items': results }), 200

def define_away_game(items):

    for item in items:
        game = item.get("game")
        
        t_home_team = game.get("Home Team", "")
        t_away_team = game.get("Away Team", "")
        j_home_team = game.get("Team Name", "")

        home_team_score = fuzz.ratio(t_home_team, j_home_team)
        away_team_score = fuzz.ratio(t_away_team, j_home_team)
    


        if home_team_score < away_team_score:
            game["away_checkbox"] = "on"
            game["away_team"] = t_home_team

        else:
            game["away_checkbox"] = ""
            game["away_team"] = t_away_team

    return items
