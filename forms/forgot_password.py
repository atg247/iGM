from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from flask import url_for, current_app
from flask_mail import Message
from helpers.extensions import mail

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


def send_reset_email(user):
    token = user.get_reset_token()

    msg = Message('Password Reset Request',
                  sender='noreply@yourapp.com',
                  recipients=[user.email])
    
    # Construct the reset URL with the generated token
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}

    If you did not make this request, please ignore this email and no changes will be made.
    '''
    # Send the email
    mail.send(msg)