from flask import jsonify, request, current_app as app
from flask_login import login_required

from helpers.game_comparison import compare_games
from logging_config import logger

from . import api_bp

def json_error(message, status=500):
    return jsonify({"status": "error", "message": message}), status

@api_bp.route('/compare', methods=['POST'])
@login_required
def compare_games_endpoint():
    logger.debug('starting compare_games_endpoint')

    # 1) Perusvarmistus: JSON-runkoinen pyyntö
    if not request.is_json:
        logger.info("compare: request content-type not JSON")
        return json_error("Virheellinen sisältötyyppi: odotettiin JSONia", 400)

    # 2) Yritä lukea JSON; jos epäonnistuu → 400
    try:
        data = request.get_json(silent=False)
    except Exception:
        app.logger.exception("compare: JSON parsing failed")
        return json_error("JSONin lukeminen epäonnistui", 400)

    # 3) Hae kentät turvallisesti ja varmista tyypit (lista).
    tulospalvelu_games = data.get('tulospalvelu_games', [])
    jopox_games = data.get('jopox_games', [])

    logger.debug(f"tulospalvelu_games: {tulospalvelu_games}")
    logger.debug(f"jopox_games: {jopox_games}")


    # 4) Suorita vertailu vain jos Jopox-dataa löytyi
    if not jopox_games:
        logger.info("compare: skipped – no jopox_games provided")
        return jsonify({
            "status": "ok",
            "data": {},
            "skipped": "no_jopox_games"
        }), 200

    # 5) Varsinainen vertailu – virheet kiinni ja lokiin stacktrace
    try:
        comparison_results = compare_games(jopox_games, tulospalvelu_games) or {}
    except Exception:
        app.logger.exception("compare: compare_games raised")
        return json_error("Vertailu epäonnistui", 502)  # Bad Gateway (ulkoisen/logic layer -tyylinen virhe)

    # 6) Onnistunut vastaus yhtenäisellä muodolla
    return jsonify(comparison_results), 200
