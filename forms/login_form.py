from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Käyttäjätunnus', validators=[DataRequired()])
    password = PasswordField('Salasana', validators=[DataRequired()])
    remember = BooleanField('Muista kirjautumiseni')  # Add the "Remember Me" checkbox
    submit = SubmitField('Kirjaudu')
