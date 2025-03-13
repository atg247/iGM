import logging

from flask import request, jsonify
from flask_login import login_required, current_user

from extensions import db
from models.userteam import UserTeam

from . import dashboard_bp

@dashboard_bp.route('/dashboard/remove_teams', methods=['POST'])
@login_required
def remove_teams():
    data = request.get_json()
    selected_teams = data.get('teams', [])

    try:
        for team in selected_teams:
            team_id = team['team_id']
            relationship_type = team['relationship_type']
            
            if relationship_type == 'jopox':
                current_user.jopox_team_id = None
                current_user.jopox_team_name = None
                db.session.commit()
                continue
            
            # Find and delete the specific UserTeam relationship
            user_team = UserTeam.query.filter_by(
                user_id=current_user.id,
                team_id=team_id,
                relationship_type=relationship_type
            ).first()
            if user_team:
                db.session.delete(user_team)

        db.session.commit()
        
        # Fetch updated lists of managed and followed teams
        managed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "id": team.id}
            for team in current_user.teams if team.team_user_entries[0].relationship_type == 'manage'
        ]
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "id": team.id}
            for team in current_user.teams if team.team_user_entries[0].relationship_type == 'follow'
        ]

        jopox_managed_team = current_user.jopox_team_name
      
        return jsonify({
            "message": "Selected teams removed successfully!",
            "managed_teams": managed_teams,
            "jopox_managed_team": jopox_managed_team,
            "followed_teams": followed_teams
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print("Error during team removal:", e)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
