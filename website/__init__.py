from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()
DB_NAME = 'database.sqlite3'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-later'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:/// {DB_NAME}'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_Views = 'auth.login'

    from .models import Customer

    @login_manager.user_loader
    def load_user(user_id):
        return Customer.query.get(int(user_id))

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    with app.app_context():
        db.create_all()
        print('Database created')

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

    return app