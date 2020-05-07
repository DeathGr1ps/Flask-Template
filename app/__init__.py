from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment


import logging
from logging.handlers import SMTPHandler

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
#Sets the view function for the login page (what page has the login form)
login.login_view = 'login'
bootstrap = Bootstrap(app)
moment = Moment(app)

from app import routes, models