from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object('config')
print app.config
db = SQLAlchemy(app)
s = db.session

from app import views

