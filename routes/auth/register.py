from flask import render_template, redirect, url_for, flash
from flask_login import current_user

from extensions import db, bcrypt
from models.user import User
from forms.registration_form import RegistrationForm

from . import auth_bp

@auth_bp.route('/register', methods=['GET', 'POST'])
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
