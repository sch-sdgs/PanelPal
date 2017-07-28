from app.queries import *
from flask_login import current_user
from flask_wtf import Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import TextField, SubmitField, HiddenField, RadioField, SelectField, FileField
from wtforms.validators import Required, regexp

from app import models
from app.panel_pal import s


def projects():
    return s.query(models.Projects).filter(
        models.Projects.user.any(models.UserRelationships.user.has(models.Users.username == current_user.id))).all()


def panels():
    return s.query(models.Panels)

def panels_unlocked():
    return s.query(models.Panels).filter(and_(models.Panels.project.has(
        models.Projects.user.any(models.UserRelationships.user.has(models.Users.username == current_user.id))), models.Panels.locked == None)).all()


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

class CreatePanel(Form):
    project = QuerySelectField(query_factory=projects,get_label='name')
    panelname = TextField("Panel Name")
    listgenes = HiddenField("Selected Genes")
    genes = TextField("Genes")
    submit = SubmitField("Create Panel")

class CreatePanelProcess(Form):
    project = QuerySelectField(query_factory=projects, get_label='name', allow_blank=True, blank_text=u'-- please choose a project -- ')
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
    panel = QuerySelectField(query_factory=panels_unlocked, get_label='name', allow_blank=True, blank_text=u'-- please choose a panel -- ')
    vpanelname = TextField("Virtual Panel Name", [Required("Enter a Virtual Panel Name")])
    make_live = RadioField(label='Do you want to make this panel live?', choices=[(True,"Yes"), (False,"No")], default=False)
    submitname = SubmitField("Complete Panel")

class EditVirtualPanelProcess(Form):
    panel = SelectField()
    vpanelname = TextField("Virtual Panel Name")
    make_live = RadioField(label='Do you want to make this panel live?', choices=[(True, "Yes"), (False, "No")],
                           default=False)
    submitname = SubmitField("Complete Edit")