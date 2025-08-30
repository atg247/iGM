from flask import request, jsonify
from flask_login import login_required, current_user

from extensions import db

from . import dashboard_bp
from logging_config import logger

#select the jopox team id for user account
@dashboard_bp.route('/dashboard/select_jopox_team', methods=['POST'])
@login_required
def select_jopox_team():
    logger.debug("select_jopox_team called")
    data = request.get_json()

    jopox_team_id = data.get('jopoxTeamId')
    jopox_team_name = data.get('jopoxTeamName')
    current_user.jopox_team_id = jopox_team_id
    current_user.jopox_team_name = jopox_team_name
    db.session.commit()
    logger.info("Jopox team selected successfully")
    return jsonify({"message": "Jopox team selected successfully!"}), 200
