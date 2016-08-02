from flask.ext.wtf import Form
from wtforms.fields import TextField, TextAreaField, SubmitField
from wtforms.validators import Required

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