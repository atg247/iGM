from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField('Käyttäjätunnus', validators=[DataRequired(), Length(min=2, max=30)])
    email = StringField('Sähköpostiosoite', validators=[DataRequired(), Email()])
    password = PasswordField('Salasana', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Vahvista salasana', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Rekisteröidy')
