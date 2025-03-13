from flask import render_template
from flask_login import login_required, current_user
from models.team import Team
from models.userteam import UserTeam 
from extensions import db
from app import app

from . import dashboard_bp

# Dashboard route (requires login)
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Get managed and followed teams for the current user
    managed_teams = db.session.query(Team).join(UserTeam).filter(
        UserTeam.user_id == current_user.id,
        UserTeam.relationship_type == 'manage'
    ).all()
    app.logger.info(f"Managed teams: {managed_teams}")
    app.logger.debug(f"Managed teams raw data: {managed_teams}")

    followed_teams = db.session.query(Team).join(UserTeam).filter(
        UserTeam.user_id == current_user.id,
        UserTeam.relationship_type == 'follow'
    ).all()
    app.logger.info(f"Followed teams: {followed_teams}")
    app.logger.debug(f"Followed teams raw data: {followed_teams}")


    jopox_data = {
        'login_url': current_user.jopox_login_url,
        'username': current_user.jopox_username,
        'password_saved': current_user.jopox_password is not None,
    }

    return render_template('dashboard.html', managed_teams=managed_teams, followed_teams=followed_teams, jopox_data=jopox_data)



    




