import os
import pandas as pd
import requests
from helpers.data_fetcher import get_levels, get_stat_groups, get_teams, hae_kalenteri
from helpers.game_fetcher import GameFetcher
from helpers.jopox_scraper import JopoxScraper
from helpers.game_comparison import compare_games
from models.db import db
from models.user import User
from models.userteam import UserTeam
from models.team import Team
from models.tgames import TGamesdb
from helpers.extensions import mail  # Import mail from extensions
from dotenv import load_dotenv
from flask_migrate import Migrate
import logging
from sqlalchemy import and_
from cryptography.fernet import Fernet
from flask import request, jsonify

from extensions import bcrypt, mail, login_manager, session
from routes.auth.auth import auth_bp




# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object('config.Config')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # Add secret key for sessions
mail.init_app(app)

app.config['SESSION_TYPE'] = 'filesystem'  # Vaihtoehdot: 'filesystem', 'redis', 'memcached', 'mongodb', jne.
app.config['SESSION_PERMANENT'] = False  # Istunto ei ole pysyvä (se nollautuu selainistunnon päättyessä)
app.config['SESSION_USE_SIGNER'] = True  # Lisää turvakerroksen session arvoihin
app.config['SESSION_FILE_DIR'] = './flask_session'  # Määritä hakemisto, jossa session tiedot tallennetaan

app.register_blueprint(auth_bp)

#MUISTA POISTAA TÄMÄ VALMIISTA VERSIOSTA!!!!!!!!!!!!!!!!!!!!!!!!
# Set logging level to DEBUG

logging.basicConfig(
        level=logging.DEBUG,
        filename="comparison.log",
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

app.logger.setLevel(logging.DEBUG)
#MUISTA POISTAA TÄMÄ VALMIISTA VERSIOSTA!!!!!!!!!!!!!!!!!!!!!!!!

# Luodaan ja tallennetaan salausavain (tämä tulisi olla turvassa palvelimella)

fernet_key = os.getenv('FERNET_KEY')
# Luo Fernet-objekti
cipher_suite = Fernet(fernet_key)


# Initialize necessary extensions
db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to 'login' if trying to access a page without being logged in

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



# Create tables if they do not exist (for simplicity)
with app.app_context():
    db.create_all()


@app.route('/test_session')
def test_session():
    session['test'] = 'Session toimii!'
    return jsonify({"message": session.get('test')})

@app.route('/schedule')
@login_required
def schedule():
    return render_template('otteluhaku.html')
  

@app.route('/')
@login_required
def index_logged():
    return render_template('index_logged.html')

@app.route('/aloitus')
def index():
    return render_template('index.html')

@app.route('/gamefetcher')
def gamefetcher():
    return render_template('gamefetcher.html')

# Route to fetch levels for a given season.
@app.route('/gamefetcher/get_levels/<season>')
def get_levels_endpoint(season):
    levels = get_levels(season)
    return jsonify(levels)

# Route to fetch statistic groups for a given level.
@app.route('/gamefetcher/get_statgroups/<season>/<level_id>/<district_id>')
def get_statgroups(season, level_id, district_id=0):
    stat_groups = get_stat_groups(season, level_id, district_id)
    return jsonify(stat_groups)

# Route to fetch teams for a given statistic group.
@app.route('/gamefetcher/get_teams/<season>/<stat_group_id>')
def get_teams_endpoint(season, stat_group_id):
    teams = get_teams(season, stat_group_id)
    return jsonify(teams)

# Route to handle form data submission to fetch games.
@app.route('/gamefetcher/fetch_games', methods=['POST'])
def fetch_games():
    print('game fetcher started')
    dwl = 0
    season = request.form['season']
    stat_group_id = request.form['statgroup']
    distr_id = 0  
    GameDates = 3
    dog = '2024-10-12'
    selected_teams = request.form.getlist('teams')

    managed_games_df = pd.DataFrame()
    if not selected_teams:
        return jsonify({"error": "No teams selected. Please choose at least one team."})

    for team_id in selected_teams:
        fetcher = GameFetcher(dwl, season, stat_group_id, team_id, distr_id, GameDates, dog)
        error = fetcher.fetch_games()

        if error:
            return jsonify({"error": error})  # Return the error in JSON format

        games_df = fetcher.display_games()
        if not games_df.empty:
            managed_games_df = pd.concat([managed_games_df, games_df], ignore_index=True)

    if managed_games_df.empty:
        return jsonify({"error": "No games found for the selected teams."})

    # Convert the games DataFrame to a JSON format
    try:
        managed_games_data = managed_games_df.to_dict(orient='records')
        return jsonify(managed_games_data)
    except Exception as e:
        return jsonify({"error": f"Error processing games data: {str(e)}"})

# Route to forward selected games.
@app.route('/gamefetcher/send_selected_games', methods=['POST'])
def send_selected_games():
    try:
        data = request.get_json()
        if not data or 'selected_games' not in data:
            return jsonify({"error": "No games selected. Please choose at least one game."}), 400
        
        selected_games = data['selected_games']
        for game in selected_games:
            print(f"Selected game details: {game}")

        return jsonify({"message": "Tämä toiminto ei ikävä kyllä ole vielä käytössä.", "games": selected_games}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Start the Flask app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
