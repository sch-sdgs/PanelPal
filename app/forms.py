from flask.ext.wtf import Form
from wtforms.fields import TextField, TextAreaField, SubmitField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required
from app import app,db,s,models


class UserForm(Form):
    name = TextField("Username",  [Required("Enter a Username")])
    submit = SubmitField("Send")


class ProjectForm(Form):
    name = TextField("Project",  [Required("Enter a Project")])
    submit = SubmitField("Send")

class RemoveGene(Form):
    geneName = TextField("Gene Name")
    panelId = TextField("Panel ID")
    submit = SubmitField("Remove Gene")

class AddGene(Form):
    geneNameAdd = TextField("Gene Name")
    panelIdAdd = TextField("Panel ID")
    submit = SubmitField("Add Gene")

def projects():
    return s.query(models.Projects)

class CreatePanel(Form):
    project = QuerySelectField(query_factory=projects,get_label='name')
    panelname = TextField("Panel Name")
    listgenes = TextAreaField("Selected Genes",)
    genes = TextField("Genes")
    submit = SubmitField("Create Panel")