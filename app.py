import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from helpers.data_fetcher import get_levels, get_stat_groups, get_teams, hae_kalenteri
from helpers.game_fetcher import GameFetcher
from models.user import db, User, Team, UserTeam
from forms.registration_form import RegistrationForm
from forms.login_form import LoginForm
from forms.forgot_password import ForgotPasswordForm, send_reset_email
from forms.reset_password import ResetPasswordForm  
from helpers.extensions import mail  # Import mail from extensions
from dotenv import load_dotenv
from flask_migrate import Migrate
import logging
from flask_mail import Mail


# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object('config.Config')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # Add secret key for sessions
mail.init_app(app)

#MUISTA POISTAA TÄMÄ VALMIISTA VERSIOSTA!!!!!!!!!!!!!!!!!!!!!!!!
# Set logging level to DEBUG
app.logger.setLevel(logging.DEBUG)
#MUISTA POISTAA TÄMÄ VALMIISTA VERSIOSTA!!!!!!!!!!!!!!!!!!!!!!!!


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

@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
        else:
            flash('No account with that email exists.', 'warning')
        return redirect(url_for('login'))
    return render_template('forgot_password.html', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

# Dashboard route (requires login)
@app.route('/dashboard')
@login_required
def dashboard():
    # Get managed and followed teams for the current user
    managed_teams = db.session.query(Team).join(UserTeam).filter(
        UserTeam.user_id == current_user.id,
        UserTeam.relationship_type == 'manage'
    ).all()
    app.logger.info(f"Managed teams: {managed_teams}")
    app.logger.debug(f"Managed teams raw data: {managed_teams}")

    followed_teams = db.session.query(Team).join(UserTeam).filter(
        UserTeam.user_id == current_user.id,
        UserTeam.relationship_type == 'follow'
    ).all()
    app.logger.info(f"Followed teams: {followed_teams}")
    app.logger.debug(f"Followed teams raw data: {followed_teams}")

    return render_template('dashboard.html', managed_teams=managed_teams, followed_teams=followed_teams)



@app.route('/dashboard/update_teams', methods=['POST'])
@login_required
def update_teams():
    try:
        data = request.get_json()
        action = data.get('action')  # Either "manage" or "follow"
        selected_teams = data.get('teams', [])
        season = data.get('season')
        level_id = data.get('level_id')
        statgroup = data.get('statgroup')

        # Check for missing fields
        if not selected_teams:
            flash("No teams selected. Please choose at least one team.", "warning")
            return jsonify({"message": "No teams selected. Please choose at least one team."}), 400

        # Process each selected team
        for team_data in selected_teams:
            team_id = team_data.get('TeamID')
            team_abbrv = team_data.get('TeamAbbrv')
            team_association = team_data.get('TeamAssociation')
            stat_group = team_data.get('stat_group')

            # Check if the team exists in the Team table; if not, add it
            team = Team.query.filter_by(team_id=team_id).first()
            if not team:
                team = Team(team_id=team_id, team_name=team_abbrv, stat_group=stat_group)
                db.session.add(team)
                db.session.commit()  # Commit here to generate `team.id` for relationships

            # Check if the relationship exists in the UserTeam table
            existing_relationship = UserTeam.query.filter_by(
                user_id=current_user.id,
                team_id=team.id,
                relationship_type=action
            ).first()

            # Create a new relationship if none exists
            if not existing_relationship:
                new_relationship = UserTeam(
                    user_id=current_user.id,
                    team_id=team.id,
                    relationship_type=action
                )
                db.session.add(new_relationship)

        db.session.commit()  # Commit all new relationships in bulk

        # Fetch the updated lists of managed and followed teams
        managed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in current_user.teams if team.team_user_entries[0].relationship_type == 'manage'
        ]
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in current_user.teams if team.team_user_entries[0].relationship_type == 'follow'
        ]
        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error during update:", e)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route('/dashboard/remove_teams', methods=['POST'])
@login_required
def remove_teams():
    data = request.get_json()
    selected_teams = data.get('teams', [])

    try:
        for team in selected_teams:
            team_id = team['team_id']
            relationship_type = team['relationship_type']

            # Find and delete the specific UserTeam relationship
            user_team = UserTeam.query.filter_by(
                user_id=current_user.id,
                team_id=team_id,
                relationship_type=relationship_type
            ).first()
            if user_team:
                db.session.delete(user_team)

        db.session.commit()
        
        # Fetch updated lists of managed and followed teams
        managed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "id": team.id}
            for team in current_user.teams if team.team_user_entries[0].relationship_type == 'manage'
        ]
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "id": team.id}
            for team in current_user.teams if team.team_user_entries[0].relationship_type == 'follow'
        ]
      
        return jsonify({
            "message": "Selected teams removed successfully!",
            "managed_teams": managed_teams,
            "followed_teams": followed_teams
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print("Error during team removal:", e)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route('/dashboard/get_ManagedFollowed', methods=['GET'])
@login_required
def get_ManagedFollowed():
    
   # Retrieves the latest managed and followed teams for the current user.
    try:
        # Fetch the managed teams
        managed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'manage').all()
        ]

        # Fetch the followed teams
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'follow').all()
        ]

        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams
        }), 200

    except Exception as e:
        print("Error fetching teams:", e)
        return jsonify({"message": f"An error occurred while fetching teams: {str(e)}"}), 500


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
    print('game fetcher started')
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
