from app.queries import *
from flask.ext.wtf import Form
from wtforms.fields import TextField, SubmitField, HiddenField, PasswordField, RadioField, BooleanField, SelectField
from wtforms.validators import Required


class UserForm(Form):
    name = TextField("Username",  [Required("Enter a Username")])
    admin = BooleanField("Admin")
    submit = SubmitField("Send")


class Search(Form):
    categories = [("Genes",'Gene'), ("Transcripts",'Transcript'), ("Panels",'Panel'), ("VPanels",'Virtual Panel'), ("Projects",'Project'), ("Users",'User')]
    search_term = TextField("Search term")
    tables = SelectField("Type", choices=categories)
    submit = SubmitField("Search")


class PrefTxCreate(Form):
    gene = RadioField(u'Genes',choices=[],coerce=int)
    project_id = TextField("Project ID")


class Login(Form):
    username  = TextField("Username")
    password = PasswordField("Password")
    submit = SubmitField("Login")
    next = HiddenField("Next")

