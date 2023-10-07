# This code is importing necessary modules and setting up the base directory for the application.
import os
from os import environ, path
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))

# `load_dotenv(path.join(basedir,".env"))` is a function call that loads the environment variables
# from a file named `.env` located in the same directory as the script. The
# `path.join(basedir,".env")` part constructs the absolute path to the `.env` file by joining the
# `basedir` (which is the absolute path to the directory containing the script) with the `.env` file
# name. The `load_dotenv()` function then reads the contents of the `.env` file and sets the
# environment variables accordingly.
load_dotenv(path.join(basedir,".env"))

# The Config class contains configuration settings for a Python application, including the secret key,
# database URI, upload folder, and SQLAlchemy settings.
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')
    UPLOAD_FOLDER ='static/img'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = "testvec26@gmail.com"
    MAIL_PASSWORD = "uuue qirf lwtf bouz"
    MAIL_DEFAULT_SENDER = 'testvec26@gmail.com' 