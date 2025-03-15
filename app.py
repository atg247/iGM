import os
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from logging_config import logger
from extensions import bcrypt, mail, login_manager, session, db
from route import routes_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from models.user import User 


def create_app():
    if os.path.exists('.env'):
        load_dotenv()

    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    session.init_app(app)
    login_manager.init_app(app)

    Migrate(app, db)

    app.register_blueprint(routes_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


    logger.info('App created successfully')


    return app

# Start the Flask app
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
