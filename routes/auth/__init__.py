# routes/auth/__init__.py

from flask import Blueprint
from flask_login import LoginManager

from extensions import db
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


from .login import *
from .register import *
from .logout import *
from .password_reset import *
from .forgot_password import *