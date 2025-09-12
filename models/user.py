from flask import current_app
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer

from extensions import db


# User Table
class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    jopox_team_id = db.Column(db.String(100), nullable=True)  # Id of the team managed in Jopox
    jopox_team_name = db.Column(db.String(50), nullable=True)  # Name of the team managed in Jopox
    jopox_login_url = db.Column(db.String(150), nullable=True)  # URL for Jopox login
    jopox_calendar_url = db.Column(db.String(150), nullable=True)  # URL for Jopox calendar
    jopox_username = db.Column(db.String(50), nullable=True)
    jopox_password = db.Column(db.LargeBinary, nullable=True)  # Salattu salasana
    # number of logins
    login_count = db.Column(db.Integer, default=0)
    # last login timestamp
    last_login = db.Column(db.DateTime, nullable=True)


    # Relationship to teams through UserTeam table
    teams = db.relationship('Team', secondary='user_team', back_populates='users', overlaps="user_team_entries,team_user_entries")

    # Password Management Methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset-salt', max_age=expires_sec)['user_id']
        except Exception as e:
            print("Token verification error:", e)  # Optional: Log the specific error
            return None
        return User.query.get(user_id)



     

