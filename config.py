import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')  # Fallback for development

    # Get the DATABASE_URL and modify if necessary
    uri = os.getenv('DATABASE_URL', 'sqlite:///hockey_data.db')
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REMEMBER_COOKIE_DURATION = timedelta(days=3)
    REMEMBER_COOKIE_SECURE = os.getenv('COOKIE_SECURE')  # True for Heroku, False locally

print("Database URL:", os.getenv('DATABASE_URL'))

