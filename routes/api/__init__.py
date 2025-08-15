# routes/api/__init__.py

from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from .get_all_schedules import *
from .get_jopox_games import *
from .get_tulospalvelu_games import *
from .get_user_teams import *
from .jopox_form_information import *
from .t_form_fetchers import *
from .update_jopox import *
from .compare import *
from .create_jopox import *
from .check_level import *
from .jopox_status import *
from werkzeug.exceptions import HTTPException

@api_bp.errorhandler(Exception)

def handle_any_error(e):
    # Jos Flask/werkzeugin oma HTTP‑poikkeus, käytä sen statuskoodia
    if isinstance(e, HTTPException):
        app.logger.warning("HTTPException in API", exc_info=e)
        return jsonify({"status": "error", "message": e.name}), e.code

    # Muut (odottamattomat) virheet
    app.logger.exception("Unhandled exception in API")
    return jsonify({"status": "error", "message": "Internal Server Error"}), 500