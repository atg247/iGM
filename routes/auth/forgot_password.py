from flask import flash, redirect, render_template, url_for

from forms.forgot_password_form import ForgotPasswordForm, send_reset_email
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
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html', form=form)
