from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
s = db.session

from app.mod_admin.views import admin

app.register_blueprint(admin)

