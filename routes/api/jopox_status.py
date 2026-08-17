from flask import jsonify
from flask_login import current_user, login_required

from extensions import db
from models.user import User

from . import api_bp


@api_bp.route("/jopox_status", methods=["GET"])
@login_required
def jopox_status():
    user = db.session.get(User, current_user.id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    active = bool(user.jopox_username and user.jopox_password)

    return jsonify({"status": "ok", "active": active}), 200
