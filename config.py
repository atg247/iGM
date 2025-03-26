import os

from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')
sqlite_path = os.path.join(instance_dir, 'hockey_data.db')

class Config:

    uri = os.getenv('DATABASE_URL')
    if not uri:
        uri = f"sqlite:///{sqlite_path}"

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REMEMBER_COOKIE_DURATION = timedelta(days=3)
    REMEMBER_COOKIE_SECURE = os.getenv('COOKIE_SECURE')  # True for Heroku, False locally

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

    # Initialize the Flask app
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # Add secret key for sessions
    SESSION_TYPE = 'filesystem'  # Vaihtoehdot: 'filesystem', 'redis', 'memcached', 'mongodb', jne.
    SESSION_PERMANENT = False  # Istunto ei ole pysyvä (se nollautuu selainistunnon päättyessä)
    SESSION_USE_SIGNER = True  # Lisää turvakerroksen session arvoihin
    SESSION_FILE_DIR = './flask_session'  # Määritä hakemisto, jossa session tiedot tallennetaan
