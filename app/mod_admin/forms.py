from flask_wtf import Form
from wtforms.fields import TextField, SubmitField, BooleanField
import wtforms.validators as valid

from app.panel_pal import s
from app.models import *

def users():
    return s.query(Users)

class UserForm(Form):
    """
    Form for adding new users to the database

    Contains a text field for the name
    """
    name = TextField("Username",  [valid.InputRequired(message="Enter a Username")])
    admin = BooleanField("Admin")
    submit = SubmitField("Send")

class NewTxForm(Form):
    """
    Form for adding a new tx to the database
    """
    accession = TextField("NCBI Accession", [valid.Regexp('N[MR]_\d+\.\d', message="Please enter an accession in the correct format, including version number (e.g. NM_000123.1)")])
    submit = SubmitField("Submit")