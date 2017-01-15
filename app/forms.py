from flask.ext.wtf import Form
from wtforms.fields import TextField, TextAreaField, SubmitField, HiddenField, PasswordField, RadioField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required
from app.main import app,db,s
from app import models
from queries import *
from flask.ext.login import LoginManager, UserMixin, \
    login_required, login_user, logout_user, current_user

class UserForm(Form):
    name = TextField("Username",  [Required("Enter a Username")])
    admin = BooleanField("Admin")
    submit = SubmitField("Send")


class ProjectForm(Form):
    name = TextField("Project Name",  [Required("Enter a Project")])
    submit = SubmitField("Create Project")

class RemoveGene(Form):
    geneName = TextField("Gene Name")
    panelId = TextField("Panel ID")
    submit = SubmitField("Remove Gene")

class AddGene(Form):
    genes = TextField("Gene Name")
    panelIdAdd = HiddenField("Panel ID")
    submit = SubmitField("Add Gene")

def projects():
    return s.query(models.Projects).filter(models.Projects.user.any(models.UserRelationships.user.has(models.Users.username == current_user.id))).all()

def panels():
    return s.query(models.Panels)

class CreatePanel(Form):
    project = QuerySelectField(query_factory=projects,get_label='name')
    panelname = TextField("Panel Name")
    listgenes = HiddenField("Selected Genes")
    genes = TextField("Genes")
    submit = SubmitField("Create Panel")

class CreateVirtualPanel(Form):
    panel = QuerySelectField(query_factory=panels,get_label='name')
    vpanelname = TextField("Virtual Panel Name", [Required("Enter a Virtual Panel Name")])
    submit = SubmitField("Create Virtual Panel")

class SelectVPGenes(Form):
    pass
    #genes = BooleanField(choices=[])

class CreateVirtualPanelProcess(Form):
    panel = QuerySelectField(query_factory=panels, get_label='name')
    vpanelname = TextField("Virtual Panel Name", [Required("Enter a Virtual Panel Name")])
    submitname = SubmitField("Begin")

class PrefTxCreate(Form):
    gene = RadioField(u'Genes',choices=[],coerce=int)
    project_id = TextField("Project ID")


class Login(Form):
    username  = TextField("Username")
    password = PasswordField("Password")
    submit = SubmitField("Login")
    next = HiddenField("Next")

def users():
    return s.query(models.Users)

class EditPermissions(Form):
    user_id  = QuerySelectField(query_factory=users,get_label='username')
    project_id = HiddenField("Project Id")
    submit = SubmitField("Grant Permission")

