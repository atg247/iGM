from flask import session, render_template, redirect, url_for, flash
from flask_login import login_user, current_user
from datetime import datetime

from extensions import bcrypt, db
from models.user import User
from models.team import Team
from models.userteam import UserTeam
from forms.login_form import LoginForm

from . import auth_bp

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        session.clear()
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)  # Pass "remember" flag to login_user()
            flash('You have successfully logged in!', 'success')

            # Log the login event
            user.login_count += 1
            user.last_login = datetime.now()
            db.session.commit()

            #check if user has managed or followed teams and redirect to dashboard
            managed_teams = db.session.query(Team).join(UserTeam).filter(
                UserTeam.user_id == user.id,
                UserTeam.relationship_type == 'manage'
            ).all()
            followed_teams = db.session.query(Team).join(UserTeam).filter(
                UserTeam.user_id == user.id,
                UserTeam.relationship_type == 'follow'
            ).all()
            if managed_teams or followed_teams:
                return redirect(url_for('routes.schedule'))
            else:
                return redirect(url_for('routes.dashboard')) 
            
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html', form=form)
