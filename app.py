import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from helpers.data_fetcher import get_levels, get_stat_groups, get_teams, hae_kalenteri
from helpers.game_fetcher import GameFetcher
from models.user import db, User
from forms.registration_form import RegistrationForm
from forms.login_form import LoginForm
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables from .env file if it exists
# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object('config.Config')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # Add secret key for sessions

# Initialize necessary extensions
db.init_app(app)
bcrypt = Bcrypt(app)

migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to 'login' if trying to access a page without being logged in

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables if they do not exist (for simplicity)
with app.app_context():
    db.create_all()

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Check if the email already exists in the database
            existing_user_email = User.query.filter_by(email=form.email.data).first()
            if existing_user_email:
                flash('An account with that email already exists. Please choose a different email.', 'danger')
                return render_template('register.html', form=form)
            
            # Check if the username already exists in the database
            existing_user_username = User.query.filter_by(username=form.username.data).first()
            if existing_user_username:
                flash('An account with that username already exists. Please choose a different username.', 'danger')
                return render_template('register.html', form=form)

            # If the email and username are unique, create the user
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()  # Only commit if no exceptions raised
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            # Rollback the session to prevent any corrupted state
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)  # Pass "remember" flag to login_user()
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html', form=form)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out.', 'info')
    return redirect(url_for('index'))

# Dashboard route (requires login)
@app.route('/dashboard')
@login_required
def dashboard():
    managed_teams = current_user.managed_teams.split(",") if current_user.managed_teams else []
    followed_teams = current_user.followed_teams.split(",") if current_user.followed_teams else []
    return render_template('dashboard.html', 
                           username=current_user.username, 
                           managed_teams=managed_teams, 
                           followed_teams=followed_teams)


@app.route('/dashboard/update_teams', methods=['POST'])
@login_required
def update_teams():
    action = request.form['action']
    selected_teams = request.form.getlist('teams')
    print(selected_teams)

    if not selected_teams:
        flash("No teams selected. Please choose at least one team.", "warning")
        return redirect(url_for('dashboard'))

    if action == 'manage':
        existing_teams = current_user.managed_teams.split(",") if current_user.managed_teams else []
        updated_teams = list(set(existing_teams + selected_teams))  # Avoid duplicate entries
        current_user.managed_teams = ",".join(updated_teams)
    elif action == 'follow':
        existing_teams = current_user.followed_teams.split(",") if current_user.followed_teams else []
        updated_teams = list(set(existing_teams + selected_teams))  # Avoid duplicate entries
        current_user.followed_teams = ",".join(updated_teams)

    try:
        db.session.commit()
        flash("Teams updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating teams: {str(e)}", "danger")

    return redirect(url_for('dashboard'))

@app.route('/jopox_ottelut')
def jopox_ottelut():
    return render_template('jopox_ottelut.html')

@app.route('/jopox_ottelut/hae_kalenteri', methods=['GET'])
@login_required
def hae_kalenteri_endpoint():
    try:
        # Fetch the events using the helper function
        events = hae_kalenteri()
        return jsonify(events)  # Return the data as JSON
    except Exception as e:
        return jsonify({"error": f"Error processing games data: {str(e)}"})

# Home page route.
@app.route('/')
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
    teams = get_teams(season, stat_group_id) # Teams': [{'TeamID': '1368627612', 'TeamAbbrv': 'Diskos Punainen', 'TeamAssociation': '10113767', 'TeamImg': '2025/10113767.png'} 
    return jsonify(teams)

# Route to handle form data submission to fetch games.
@app.route('/gamefetcher/fetch_games', methods=['POST'])
def fetch_games():
    dwl = 0
    season = request.form['season']
    stat_group_id = request.form['statgroup']
    distr_id = 0  
    GameDates = 3
    dog = '2024-10-12'
    selected_teams = request.form.getlist('teams')

    all_games_df = pd.DataFrame()
    if not selected_teams:
        return jsonify({"error": "No teams selected. Please choose at least one team."})

    for team_id in selected_teams:
        fetcher = GameFetcher(dwl, season, stat_group_id, team_id, distr_id, GameDates, dog)
        error = fetcher.fetch_games()

        if error:
            return jsonify({"error": error})  # Return the error in JSON format

        games_df = fetcher.display_games()
        if not games_df.empty:
            all_games_df = pd.concat([all_games_df, games_df], ignore_index=True)

    if all_games_df.empty:
        return jsonify({"error": "No games found for the selected teams."})

    # Convert the games DataFrame to a JSON format
    try:
        all_games_data = all_games_df.to_dict(orient='records')
        return jsonify(all_games_data)
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
