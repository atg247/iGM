from flask import jsonify
from flask_login import login_required, current_user
from models.user import User
from extensions import db
from app import app

from . import dashboard_bp

@dashboard_bp.route('/dashboard/get_jopox_credentials', methods=['GET'])
@login_required
def get_jopox_credentials():
    print("Getting Jopox credentials for user", current_user.username)
    user = db.session.get(User, current_user.id)
    jopox_data = {
        'login_url': user.jopox_login_url,
        'username': user.jopox_username,
        'password_saved': user.jopox_password is not None,}
    print(f"Jopox data: {jopox_data}")  
    return jsonify(jopox_data)
