from flask import jsonify
from flask_login import login_required, current_user

from extensions import db
from models.user import User

from . import dashboard_bp

@dashboard_bp.route('/dashboard/clear_jopox_credentials', methods=['GET'])
@login_required
def clear_jopox_credentials():
    print("Clearing Jopox credentials for user", current_user.username)
    user = db.session.get(User, current_user.id)
    user.jopox_login_url = None
    user.jopox_username = None
    user.jopox_password = None
    user.jopox_team_name = None
    user.jopox_team_id = None
    user.jopox_calendar_url = None

    db.session.commit()
    return jsonify({'message': 'Jopox credentials cleared successfully'})
