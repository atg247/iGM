from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
mail = Mail()
login_manager = LoginManager()
session = Session()
db = SQLAlchemy()

