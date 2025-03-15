from flask import Flask
from models.users import db, User
from flask_login import LoginManager
from routes.user_routes import user_bp
from routes.dashboard_routes import dashboard_bp
from routes.transaction_routes import transaction_bp

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config["SECRET_KEY"] = "your_secret_key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'user.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(user_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)

    return app
