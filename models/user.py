from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

db = SQLAlchemy()

# User Table
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
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


# Team Table
class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.String(100), unique=True, nullable=False)  # The team's unique identifier
    team_name = db.Column(db.String(150), nullable=False)
    stat_group = db.Column(db.String(150), nullable=True)
    season = db.Column(db.String(50), nullable=True)
    level_id = db.Column(db.String(50), nullable=True)
    team_association = db.Column(db.String(50), nullable=True)

    # Relationship to users through UserTeam table
    users = db.relationship('User', secondary='user_team', back_populates='teams', overlaps="user_team_entries,team_user_entries")

# UserTeam Association Table
class UserTeam(db.Model):
    __tablename__ = 'user_team'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    relationship_type = db.Column(db.String(50), nullable=False)  # 'managed' or 'followed'

    # Relationships to navigate between related items, avoiding overlaps
    user = db.relationship('User', backref=db.backref('user_team_entries', cascade='all, delete-orphan'), overlaps="teams,users")
    team = db.relationship('Team', backref=db.backref('team_user_entries', cascade='all, delete-orphan'), overlaps="users,teams")
