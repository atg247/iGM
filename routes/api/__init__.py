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