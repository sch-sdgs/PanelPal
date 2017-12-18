from flask_wtf import Form
from wtforms.fields import TextField, SubmitField, BooleanField
from wtforms.validators import Required

from app.panel_pal import s
from app.models import *

def users():
    return s.query(Users)

class UserForm(Form):
    """
    Form for adding new users to the database

    Contains a text field for the name
    """
    name = TextField("Username",  [Required("Enter a Username")])
    admin = BooleanField("Admin")
    submit = SubmitField("Send")