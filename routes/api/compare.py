import logging

from flask import jsonify, request
from flask_login import login_required

from flask import current_app as app
from helpers.game_comparison import compare_games

from . import api_bp

@api_bp.route('/compare', methods=['POST'])
@login_required
def compare_games_endpoint():

    try:
        # Receive datasets from the frontend
        logging.debug('starting compare_games_endpoint')
        data = request.get_json()
        tulospalvelu_games = data.get('tulospalvelu_games', [])
        jopox_games = data.get('jopox_games', [])
        #print("tulospalvelu_games:", tulospalvelu_games[0])
        print("jopox_games vertailua varten:", jopox_games[0])   
        # Perform the comparison
        comparison_results = compare_games(jopox_games, tulospalvelu_games)

        # Return comparison results
        return jsonify(comparison_results), 200

    except Exception as e:
        app.logger.error(f"Error in game comparison: {e}")
        return jsonify({"error": "Comparison failed", "details": str(e)}), 500
