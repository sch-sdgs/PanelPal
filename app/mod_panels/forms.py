from app.queries import *
from flask_login import current_user
from flask_wtf import FlaskForm as Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import TextField, SubmitField, HiddenField, RadioField, SelectField, FileField
from wtforms.validators import Required, regexp

from app import models
from app.panel_pal import s
from sqlalchemy import and_

def panels():
    return s.query(models.Panels)

class RemoveGene(Form):
    geneName = TextField("Gene Name")
    panelId = TextField("Panel ID")
    submit = SubmitField("Remove Gene")

class AddGene(Form):
    genes = TextField("Gene Name")
    panelIdAdd = HiddenField("Panel ID")
    submit = SubmitField("Add Gene")


class ViewPanel(Form):
    versions = SelectField("Select a version:")
    submit = SubmitField("Go")

class CreatePanelProcess(Form):
    project = SelectField("Project")
    panelname = TextField("Panel Name", [Required("Enter a Panel Name")])
    make_live = RadioField(label='Do you want to make this panel live?', choices=[(True,"Yes"), (False,"No")], default=False)
    genes = TextField("Genes")
    gene_list = FileField('', [regexp('^.+\.txt$')])
    submitname = SubmitField("Complete Panel")

class EditPanelProcess(Form):
    project = SelectField()
    panelname = TextField("Panel Name")
    make_live = RadioField(label='Do you want to make this panel live?', choices=[(True,"Yes"), (False,"No")], default=False)
    genes = TextField("Genes")
    gene_list = FileField('Gene List', [regexp('^.+\.txt$')])
    submitname = SubmitField("Complete Edit")

class CreateVirtualPanelProcess(Form):
    panel = SelectField("Panel")
    vpanelname = TextField("Virtual Panel Name", [Required("Enter a Virtual Panel Name")])
    submitname = SubmitField("Complete Panel")

class EditVirtualPanelProcess(Form):
    panel = SelectField()
    vpanelname = TextField("Virtual Panel Name")
    make_live = RadioField(label='Do you want to make this panel live?', choices=[(True, "Yes"), (False, "No")],
                           default=False)
    submitname = SubmitField("Complete Edit")