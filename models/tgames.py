#create a table for users game schedule from Tulospalvelu.fi

from extensions import db

class TGamesdb(db.Model):
    __tablename__ = 'tgames'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.String(100), db.ForeignKey('team.team_id'), nullable=False)  # Link to the team
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    home_team = db.Column(db.String(150), nullable=False)
    away_team = db.Column(db.String(150), nullable=False)
    home_goals = db.Column(db.String(50), nullable=False)
    away_goals = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    level_name = db.Column(db.String(150), nullable=False)
    stat_group_name = db.Column(db.String(50), nullable=False)
    small_area_game = db.Column(db.String(50), nullable=False)
    team_name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    sortable_date = db.Column(db.DateTime, nullable=False)



    team = db.relationship('Team', back_populates='games')  # One team to many games
