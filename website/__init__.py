import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

load_dotenv()



db = SQLAlchemy()
mail = Mail()
DB_NAME = 'database.sqlite3'


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .models import Customer

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Customer, int(user_id))

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

    from .admin import admin
    app.register_blueprint(admin, url_prefix='/')

    from .seller import seller
    app.register_blueprint(seller, url_prefix='/')

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')

    with app.app_context():
        db.create_all()
        print('Database created')

    return app