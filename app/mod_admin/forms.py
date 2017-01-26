from flask.ext.wtf import Form
from wtforms.fields import TextField, TextAreaField, SubmitField, HiddenField, PasswordField, RadioField, BooleanField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required
from app.main import s
from app.models import *

def users():
    return s.query(Users)

class EditPermissions(Form):
    user_id  = QuerySelectField(query_factory=users,get_label='username')
    project_id = HiddenField("Project Id")
    submit = SubmitField("Grant Permission")


class UserForm(Form):
    name = TextField("Username",  [Required("Enter a Username")])
    admin = BooleanField("Admin")
    submit = SubmitField("Send")