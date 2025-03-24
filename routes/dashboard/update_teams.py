from flask import request, jsonify, flash
from sqlalchemy import and_
from flask_login import login_required, current_user

from extensions import db
from models.team import Team
from models.userteam import UserTeam

from . import dashboard_bp

@dashboard_bp.route('/dashboard/update_teams', methods=['POST'])
@login_required
def update_teams():
    try:
        data = request.get_json()
        print('This is data:', data)
        action = data.get('action')  # Either "manage" or "follow"
        selected_teams = data.get('teams', [])

        # Check for missing fields
        if not selected_teams:
            flash("No teams selected. Please choose at least one team.", "warning")
            return jsonify({"message": "No teams selected. Please choose at least one team."}), 400

        # Process each selected team
        for team_data in selected_teams:
            team_id = team_data.get('TeamID')
            team_abbrv = team_data.get('TeamAbbrv')
            team_association = team_data.get('team_association')
            stat_group = team_data.get('stat_group')
            season = team_data.get('season')
            level_id = team_data.get('level_id')
            statgroup = team_data.get('statgroup')

            # Check if the team exists in the Team table for this team_id + stat_group
            team = Team.query.filter_by(team_id=team_id, stat_group=stat_group).first()
            
            if not team:
                # Create new team if it doesn't exist
                team = Team(
                    team_id=team_id,
                    team_name=team_abbrv,
                    stat_group=stat_group,
                    team_association=team_association,
                    season=season,
                    level_id=level_id,
                    statgroup=statgroup
                )
                db.session.add(team)
                db.session.commit()  # Commit to generate `team.id`

            # Check if the relationship exists in the UserTeam table for this user + team + action
            existing_relationship = UserTeam.query.filter(
                and_(
                    UserTeam.user_id == current_user.id,
                    UserTeam.team_id == team.id,
                    UserTeam.relationship_type == action
                )
            ).first()

            # Create a new relationship if none exists
            if not existing_relationship:
                new_relationship = UserTeam(
                    user_id=current_user.id,
                    team_id=team.id,
                    relationship_type=action
                )
                db.session.add(new_relationship)

        db.session.commit()  # Commit all new relationships in bulk

        # Fetch the updated lists of managed and followed teams
        managed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in current_user.teams if any(entry.relationship_type == 'manage' for entry in team.team_user_entries)
        ]
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in current_user.teams if any(entry.relationship_type == 'follow' for entry in team.team_user_entries)
        ]
        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error during update:", e)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
