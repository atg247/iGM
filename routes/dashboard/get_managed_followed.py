from flask import jsonify
from flask_login import login_required, current_user

from models.team import Team
from models.userteam import UserTeam

from . import dashboard_bp
from logging_config import logger

@dashboard_bp.route('/dashboard/get_ManagedFollowed', methods=['GET'])
@login_required
def get_ManagedFollowed():
    
   # Retrieves the latest managed and followed teams for the current user.
    try:
        # Fetch the managed teams
        managed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'manage').all()
        ]

        # Fetch the followed teams
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'follow').all()
        ]

        jopox_managed_team = current_user.jopox_team_name

        logger.debug("managed_teams:", managed_teams, "followed_teams:", followed_teams, "jopox_managed_team:", jopox_managed_team)

        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams,
            "jopox_managed_team": jopox_managed_team
        }), 200

    except Exception as e:
        logger.error("Error fetching teams: %s", e)
        return jsonify({"message": f"An error occurred while fetching teams: {str(e)}"}), 500
