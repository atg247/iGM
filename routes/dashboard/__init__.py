# routes/dashboard/__init__.py
from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__)

from .remove_teams import *
from .save_jopox_credentials import *
from .select_jopox_team import *
from .update_teams import *
from .get_managed_followed import *
from .clear_jopox_credentials import *