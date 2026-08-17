from flask import current_app as app
from flask import jsonify, request
from flask_login import login_required

from helpers.game_comparison import compare_games
from logging_config import logger
from models.tgames import TGamesdb

from . import api_bp


def load_jopox_links(tulospalvelu_games):
    """Hakee kannasta luontivaiheessa tallennetut {game_id: jopox_uid} -parit.

    Linkit luetaan kannasta eikä pyynnön rungosta, koska frontendin lähettämä data tulee
    suoraan Tulospalvelusta eikä sisällä uid:tä. Virhetilanteessa palautetaan tyhjä kartta,
    jolloin vertailu putoaa entiseen fuzzy-täsmäytykseen.
    """
    # Game ID tulee frontendilta JSON-numerona mutta on kannassa merkkijono. SQLite täsmää
    # numeron TEXT-sarakkeeseen tyyppiaffiniteetin ansiosta, joten haku näyttäisi toimivan,
    # mutta dict-avaimet jäisivät eri tyyppisiksi kuin haettaessa. Normalisoidaan molemmat
    # päät merkkijonoksi - Postgresissa vertailu ei olisi edes onnistunut.
    game_ids = [
        str(g.get('Game ID')) for g in tulospalvelu_games
        if isinstance(g, dict) and g.get('Game ID')
    ]
    if not game_ids:
        return {}

    try:
        rows = TGamesdb.query.filter(
            TGamesdb.game_id.in_(game_ids),
            TGamesdb.jopox_uid.isnot(None),
        ).all()
        return {str(row.game_id): row.jopox_uid for row in rows}
    except Exception:
        app.logger.exception("compare: failed to load jopox_uid links")
        return {}

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

    # 4) Suorita vertailu vain jos Jopox-dataa löytyi
    if not jopox_games:
        logger.info("compare: skipped – no jopox_games provided")
        return jsonify({
            "status": "ok",
            "data": {},
            "skipped": "no_jopox_games"
        }), 200

    # 5) Varsinainen vertailu – virheet kiinni ja lokiin stacktrace
    jopox_links = load_jopox_links(tulospalvelu_games)
    try:
        comparison_results = compare_games(jopox_games, tulospalvelu_games, jopox_links) or {}
    except Exception:
        app.logger.exception("compare: compare_games raised")
        return json_error("Vertailu epäonnistui", 502)  # Bad Gateway (ulkoisen/logic layer -tyylinen virhe)

    logger.info('comparison completed')

    # 6) Onnistunut vastaus yhtenäisellä muodolla
    return jsonify(comparison_results), 200
