from extensions import db

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Ensure id is the primary key and auto-incremented
    team_id = db.Column(db.String(100), nullable=False)  # Ensure team_id is unique
    team_name = db.Column(db.String(150), nullable=False)
    stat_group = db.Column(db.String(150), nullable=True)
    season = db.Column(db.String(50), nullable=True)
    level_id = db.Column(db.String(50), nullable=True)
    team_association = db.Column(db.String(50), nullable=True)
    statgroup = db.Column(db.String(50), nullable=True)

    # Relationship to users through UserTeam table
    users = db.relationship('User', secondary='user_team', back_populates='teams', overlaps="user_team_entries,team_user_entries")
    # Relationship to games
    games = db.relationship('TGamesdb', back_populates='team', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'stat_group', name='uq_team_id_stat_group'),
    )
