# UserTeam Association Table

from models.db import db

class UserTeam(db.Model):
    __tablename__ = 'user_team'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_team_user_id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', name='fk_user_team_team_id'), nullable=False)

    relationship_type = db.Column(db.String(50), nullable=False)  # 'managed' or 'followed'

    # Relationships to navigate between related items, avoiding overlaps
    user = db.relationship('User', backref=db.backref('user_team_entries', cascade='all, delete-orphan'), overlaps="teams,users")
    team = db.relationship('Team', backref=db.backref('team_user_entries', cascade='all, delete-orphan'), overlaps="users,teams")
