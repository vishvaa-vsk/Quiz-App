from flask import Flask
from .extensions import mongo,mail
from .config import Config
from datetime import timedelta
from .routes.main import main
from .routes.admin import admin

def create_app():
    """
    The function creates and configures a Flask application with a specified configuration class,
    initializes the database, registers blueprints for different parts of the application, and creates
    the necessary database tables.
    
    :param config_class: The `config_class` parameter is used to specify the configuration class for the
    Flask application. The configuration class contains various settings and options for the
    application, such as database connection details, secret keys, and other environment-specific
    configurations
    :return: an instance of the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(obj=Config)
    app.permanent_session_lifetime = timedelta(minutes=60)
 
    mail.init_app(app)
    mongo.init_app(app)

    app.register_blueprint(main)
    app.register_blueprint(admin)

    return app

