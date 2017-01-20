from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
s = db.session

from app.views import *

