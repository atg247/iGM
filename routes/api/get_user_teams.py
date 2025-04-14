from flask import jsonify
from flask_login import current_user
from flask import current_app as app

from models.team import Team
from models.userteam import UserTeam

from . import api_bp


@api_bp.route('/teams')
def get_user_teams():
    """
    Fetch managed and followed teams for the current user.
    """
    try:
        managed_teams = [
            {
                "team_name": team.team_name,
                "stat_group": team.stat_group,
                "team_id": team.team_id,
                "season": team.season,
                "level_id": team.level_id,
                "statgroup": team.statgroup,
                "type": "manage"
            }
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'manage').all()
        ]

        followed_teams = [
            {
                "team_name": team.team_name,
                "stat_group": team.stat_group,
                "team_id": team.team_id,
                "season": team.season,
                "level_id": team.level_id,
                "statgroup": team.statgroup,
                "type": "follow"
            }
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'follow').all()
        ]

        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams
        }), 200

    except Exception as e:
        app.logger.error(f"Error fetching teams: {str(e)}")
        return jsonify({"error": "Failed to fetch teams", "details": str(e)}), 500
