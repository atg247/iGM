import os
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from helpers.data_fetcher import get_levels, get_stat_groups, get_teams, hae_kalenteri
from helpers.game_fetcher import GameFetcher
from helpers.jopox_scraper import JopoxScraper
from helpers.game_comparison import compare_games
from models.user import db, User, Team, UserTeam, TGamesdb
from forms.registration_form import RegistrationForm
from forms.login_form import LoginForm
from forms.forgot_password import ForgotPasswordForm, send_reset_email
from forms.reset_password import ResetPasswordForm  
from helpers.extensions import mail  # Import mail from extensions
from dotenv import load_dotenv
from flask_migrate import Migrate
import logging
from flask_mail import Mail
from sqlalchemy import and_




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
    return db.session.get(User, int(user_id))



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
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)  # Pass "remember" flag to login_user()
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
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

#select the jopox team id for user account
@app.route('/dashboard/select_jopox_team', methods=['POST'])
@login_required
def select_jopox_team():
    data = request.get_json()
    print('This is data received with json:', data)
    jopox_team_id = data.get('jopoxTeamId')
    jopox_team_name = data.get('jopoxTeamName')
    current_user.jopox_team_id = jopox_team_id
    current_user.jopox_team_name = jopox_team_name
    db.session.commit()
    print(f"Jopox team ID {jopox_team_id} selected for user {current_user.username}. Tallennettu team id on: {current_user.jopox_team_id}/n Tallennettu team name on: {current_user.jopox_team_name}")
    return jsonify({"message": "Jopox team selected successfully!"}), 200
    

@app.route('/dashboard/update_teams', methods=['POST'])
@login_required
def update_teams():
    try:
        data = request.get_json()
        print('This is data:', data)
        action = data.get('action')  # Either "manage" or "follow"
        selected_teams = data.get('teams', [])

        # Check for missing fields
        if not selected_teams:
            flash("No teams selected. Please choose at least one team.", "warning")
            return jsonify({"message": "No teams selected. Please choose at least one team."}), 400

        # Process each selected team
        for team_data in selected_teams:
            team_id = team_data.get('TeamID')
            team_abbrv = team_data.get('TeamAbbrv')
            team_association = team_data.get('team_association')
            stat_group = team_data.get('stat_group')
            season = team_data.get('season')
            level_id = team_data.get('level_id')
            statgroup = team_data.get('statgroup')

            # Check if the team exists in the Team table for this team_id + stat_group
            team = Team.query.filter_by(team_id=team_id, stat_group=stat_group).first()
            
            if not team:
                # Create new team if it doesn't exist
                team = Team(
                    team_id=team_id,
                    team_name=team_abbrv,
                    stat_group=stat_group,
                    team_association=team_association,
                    season=season,
                    level_id=level_id,
                    statgroup=statgroup
                )
                db.session.add(team)
                db.session.commit()  # Commit to generate `team.id`

            # Check if the relationship exists in the UserTeam table for this user + team + action
            existing_relationship = UserTeam.query.filter(
                and_(
                    UserTeam.user_id == current_user.id,
                    UserTeam.team_id == team.id,
                    UserTeam.relationship_type == action
                )
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
            for team in current_user.teams if any(entry.relationship_type == 'manage' for entry in team.team_user_entries)
        ]
        followed_teams = [
            {"team_name": team.team_name, "stat_group": team.stat_group, "team_id": team.id}
            for team in current_user.teams if any(entry.relationship_type == 'follow' for entry in team.team_user_entries)
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
            
            if relationship_type == 'jopox':
                current_user.jopox_team_id = None
                current_user.jopox_team_name = None
                db.session.commit()
                continue
            
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

        jopox_managed_team = current_user.jopox_team_name
      
        return jsonify({
            "message": "Selected teams removed successfully!",
            "managed_teams": managed_teams,
            "jopox_managed_team": jopox_managed_team,
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

        jopox_managed_team = current_user.jopox_team_name

        print("managed_teams:", managed_teams, "followed_teams:", followed_teams, "jopox_managed_team:", jopox_managed_team)

        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams,
            "jopox_managed_team": jopox_managed_team
        }), 200

    except Exception as e:
        print("Error fetching teams:", e)
        return jsonify({"message": f"An error occurred while fetching teams: {str(e)}"}), 500

@app.route('/schedule')
@login_required
def schedule():

    return render_template('otteluhaku.html')

@app.route('/api/teams')
def get_user_teams():
    """
    Fetch managed and followed teams for the current user.
    """
    try:
        managed_teams = [
            {
                "team_name": team.team_name,
                "stat_group": team.stat_group,
                "team_id": team.team_id,
                "season": team.season,
                "level_id": team.level_id,
                "statgroup": team.statgroup,
                "type": "manage"
            }
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'manage').all()
        ]

        followed_teams = [
            {
                "team_name": team.team_name,
                "stat_group": team.stat_group,
                "team_id": team.team_id,
                "season": team.season,
                "level_id": team.level_id,
                "statgroup": team.statgroup,
                "type": "follow"
            }
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'follow').all()
        ]

        return jsonify({
            "managed_teams": managed_teams,
            "followed_teams": followed_teams
        }), 200

    except Exception as e:
        app.logger.error(f"Error fetching teams: {str(e)}")
        return jsonify({"error": "Failed to fetch teams", "details": str(e)}), 500


    
@app.route('/api/schedules')
def get_all_schedules():
    """
    Fetch schedules for all managed and followed teams, sorted by date and time.
    """
    try:
        managed_teams = [
            {"team_name": team.team_name, "team_id": team.team_id, "season": team.season, "stat_group_id": team.statgroup, "type": 'manage'}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'manage').all()
        ]

        followed_teams = [
            {"team_name": team.team_name, "team_id": team.team_id, "season": team.season, "stat_group_id": team.statgroup, "type": 'follow'}
            for team in Team.query.join(UserTeam)
            .filter(UserTeam.user_id == current_user.id, UserTeam.relationship_type == 'follow').all()
        ]

        all_teams = managed_teams + followed_teams
        managed_games = []

        # Fetch games for each team
        for team in all_teams:
            try:
                fetcher = GameFetcher(
                    dwl=0,  # Replace with actual value
                    season=team['season'],
                    stat_group_id=team['stat_group_id'],
                    team_id=team['team_id'],
                    distr_id=0,  # Replace with actual value if needed
                    GameDates=3,  # Replace with actual value if needed
                    dog='2024-10-12'  # Replace with actual date logic if needed
                )
                error = fetcher.fetch_games()

                if error:
                    app.logger.error(f"Error fetching games for {team['team_name']}: {error}")
                    continue  # Skip this team if there's an error

                # Format the games using display_games helper
                games_df = fetcher.display_games()
                if not games_df.empty:
                    games_df['Team Name'] = team['team_name']
                    games_df['Type'] = team['type']  # Manage or Follow

                    # Add formatted and sortable dates
                    games_df['SortableDate'] = games_df['Date']
                    games_df['Date'] = games_df['Date'].dt.strftime('%d.%m.%Y')  # Format for display
                    managed_games.extend(games_df.to_dict(orient='records'))

            except Exception as e:
                app.logger.error(f"Error fetching games for {team['team_name']}: {str(e)}")
                continue  # Skip to the next team if error occurs during fetch

        # Sort all games by sortable date and time
        managed_games = sorted(managed_games, key=lambda game: (game['SortableDate'], game['Time']))
        print("managed_games:", managed_games[:1])
        
        # Store the games in the database if not already there based on game id
        updated_games = []  # List of updated games

        for game in managed_games:
            try:
                print("adding game to db:", game)
                # Check if the game already exists
                existing_game = TGamesdb.query.filter_by(game_id=game['Game ID']).first()
                print("existing_game:", existing_game)

                if existing_game:
                    # Compare existing game and new game
                    changes = {}

                    # Check if the date has changed
                    if existing_game.date != game['Date']:
                        changes['date'] = {'old': existing_game.date, 'new': game['Date']}
                        existing_game.date = game['Date']

                    # Check if the time has changed
                    if existing_game.time != game['Time']:
                        changes['time'] = {'old': existing_game.time, 'new': game['Time']}
                        existing_game.time = game['Time']

                    # Check if the location has changed
                    if existing_game.location != game['Location']:
                        changes['location'] = {'old': existing_game.location, 'new': game['Location']}
                        existing_game.location = game['Location']

                    # If there are any changes, add this game to the updated games list
                    if changes:
                        updated_games.append({
                            'game_id': game['Game ID'],
                            'changes': changes
                        })
                else:
                    # If the game doesn't exist, add it as a new game
                    new_game = TGamesdb(
                        game_id=game['Game ID'],
                        team_id=game['Team ID'],
                        date=game['Date'],
                        time=game['Time'],
                        home_team=game['Home Team'],
                        away_team=game['Away Team'],
                        home_goals=game['Home Goals'],
                        away_goals=game['Away Goals'],
                        location=game['Location'],
                        level_name=game['Level Name'],
                        small_area_game=game['Small Area Game'],
                        team_name=game['Team Name'],
                        type=game['Type'],
                        sortable_date=game['SortableDate']
                    )
                    print(f"Attempting to add new game: {game['Game ID']}")
                    db.session.add(new_game)

            except Exception as e:
                app.logger.error(f"Error processing game {game['Game ID']}: {str(e)}")

        # Commit the changes if any games have been updated or added
        if updated_games:
            db.session.commit()
            print(f"Updated games: {updated_games}")

        return jsonify({
            "managed_games": managed_games,
            "updated_games": updated_games,
            "message": "Games processed successfully"
        }), 200

    except Exception as e:
        db.session.rollback()  # Rollback in case of any error in the outer block
        app.logger.error(f"Error fetching schedules: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    

        # Palautetaan muutokset frontendille


@app.route('/api/jopox_games')
@login_required
def get_jopox_games():
    print('starting api/jopox_games')
    try:
        # Fetch games from Jopox
        jopox_games = hae_kalenteri(current_user.jopox_team_id)
        #print("jopox_games:", jopox_games)

        # Ensure a valid response is returned
        return jsonify({"status": "success", "data": jopox_games}), 200

    except Exception as e:
        # Log the error for debugging
        app.logger.error(f"Error fetching Jopox games: {e}")

        # Return an error response
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/compare', methods=['POST'])
@login_required
def compare_games_endpoint():

    try:
        # Receive datasets from the frontend
        data = request.get_json()
        tulospalvelu_games = data.get('tulospalvelu_games', [])
        jopox_games = data.get('jopox_games', [])
        #print("tulospalvelu_games:", tulospalvelu_games[0])
        #print("jopox_games:", jopox_games[0])   
        # Perform the comparison
        comparison_results = compare_games(jopox_games, tulospalvelu_games)

        # Return comparison results
        return jsonify(comparison_results), 200

    except Exception as e:
        app.logger.error(f"Error in game comparison: {e}")
        return jsonify({"error": "Comparison failed", "details": str(e)}), 500

@app.route('/api/update_jopox', methods=['POST'])
def update_jopox():
    data = request.json
    game = data.get('game')
    best_match = data.get('best_match')

    print("Game info:", game)
    print("Jopox info:", best_match)

    username = "malkamaki.antti@gmail.com"
    password = "zorfyj-rymje5-hycsyX"

    if not best_match:
        print("No best match found.")
        try: 
            scraper = JopoxScraper(username, password)

            if scraper.login() and scraper.access_admin():
                game_data = {
                    "SeasonId": "547",
                    "SubSiteId": "8787",
                    "LeagueDropdownList": "15460", #"15116" Treenipelit 24/25, "15449" U12 Sarja lohko, "15460" U12 Sarja lohko 3B
                    "EventDropDownList": "",
                    "HomeTeamTextBox": game.get("Punainen", ""),#muokattu S-kiekko Punainen muotoon Punainen - pitää keksiä joku logiikka
                    "GuestTeamTextBox": game.get("Away Team", ""),
                    "AwayCheckbox": "", #Tämä pitää setviä kuntoon jos tyhjä niin kotijoukkue on kotijoukkue ja jos "on" niin vierasjoukkue on kotijoukkue.
                    "GameLocationTextBox": game.get("Location", ""),
                    "GameDateTextBox": game.get("Date", ""),
                    "GameStartTimeTextBox": game.get("Time", ""),
                    "GameDurationTextBox": game.get("GameDurationTextBox", "120"),
                    "GameDeadlineTextBox": "",
                    "GameMaxParticipatesTextBox": "",
                    "GamePublicInfoTextBox": f"""{'Pienpeli' if game.get('Small Area Game') == '1' else 'Ison kentän peli'}<br>
                    <br>                    
                    Kokoontuminen tuntia ennen ottelun alkua.<br>
                    <br>
                    Joukkue:
                    <br>
                    """,#Tähän kenttään logiikka, jolla määritetään tarvitaanko toimitsijoita ja niin, että huomioi pienpelit
                    "FeedGameDropdown": "0",
                    "GameInfoTextBox": f"""
                    Ottelu {game.get('Date')} klo {game.get('Time')}<br>
                    {game.get('Home Team')} - {game.get('Away Team')}<br>
                    {game.get('Location')}<br><br>Kaikki joukkueen jäsenet""",
                    "GameNotificationTextBox": "",
                    "SaveGameButton": "Tallenna"
                    }
            
                #scraper.add_game(game_data)
                return jsonify({"message": "Pelin lisäämistoiminto ei käytössä, aktivoi scraper.add_game."}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    else:
        print("Skippasi tänne.")


@app.route('/jopox_ottelut')
@login_required
def jopox_ottelut():
    return render_template('jopox_ottelut.html')

@app.route('/jopox_ottelut/hae_kalenteri', methods=['GET'])
@login_required
def hae_kalenteri_endpoint():
    try:
        # Fetch the events using the helper function
        events = hae_kalenteri(current_user.jopox_team_id)
        return jsonify(events)  # Return the data as JSON
    except Exception as e:
        return jsonify({"error": f"Error processing games data: {str(e)}"})

# Home page route.
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
