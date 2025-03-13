from flask import render_template, redirect, url_for, flash
from forms.forgot_password_form import ForgotPasswordForm
from forms.forgot_password_form import send_reset_email
from models.user import User

from . import auth_bp

@auth_bp.route("/forgot_password", methods=['GET', 'POST'])
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
