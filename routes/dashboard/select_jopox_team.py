from flask import request, jsonify
from flask_login import login_required, current_user

from extensions import db

from . import dashboard_bp

#select the jopox team id for user account
@dashboard_bp.route('/dashboard/select_jopox_team', methods=['POST'])
@login_required
def select_jopox_team():
    data = request.get_json()
    print('This is data received with json:', data)
    jopox_team_id = data.get('jopoxTeamId')
    jopox_team_name = data.get('jopoxTeamName')
    current_user.jopox_team_id = jopox_team_id
    current_user.jopox_team_name = jopox_team_name
    db.session.commit()
    print(f"Jopox team ID {jopox_team_id} selected for user {current_user.username}. Tallennettu team id on: {current_user.jopox_team_id}/n Tallennettu team name on: {current_user.jopox_team_name}")
    return jsonify({"message": "Jopox team selected successfully!"}), 200
