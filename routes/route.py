#route.py

from flask import Blueprint, render_template, jsonify, session
from flask_login import login_required
from flask import current_app as app

from models.team import Team
from models.userteam import UserTeam
from extensions import db
from flask_login import current_user
from logging_config import logger
from helpers import update_jopox_credentials


routes_bp = Blueprint('routes', __name__, static_folder="static", template_folder="templates")

@routes_bp.route('/test_session')
def test_session():
    session['test'] = 'Session toimii!'
    return jsonify({"message": session.get('test')})

@routes_bp.route('/schedule')
@login_required
def schedule():
    update_jopox_credentials()
    return render_template('otteluhaku.html')
  
@routes_bp.route('/')
def index():
    logger.debug('Index route')
    if 'user_id' in session:
        return index_logged()
    else:
        return render_template('index.html')

def index_logged():
    return render_template('index_logged.html')

@routes_bp.route('/gamefetcher')
def gamefetcher():
    return render_template('gamefetcher.html')

@routes_bp.route('/dashboard')
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

