from flask_wtf import Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import TextField, SubmitField, HiddenField, SelectField
from wtforms.validators import Required

from app.panel_pal import s
from app.models import *
from producers.StarLims import StarLimsApi

def get_serv_grp():
    starlims = StarLimsApi()
    serv_grp = starlims.get_all_serv()
    choices = []
    for grp in serv_grp:
        choices.append((grp['SERVGRPCODE'], grp['SERVGRP']))

    return choices

class ProjectForm(Form):
    name = SelectField('Project Name', choices=get_serv_grp())
    submit = SubmitField("Create Project")


def users():
    return s.query(Users)

class EditPermissions(Form):
    user_id  = QuerySelectField(query_factory=users,get_label='username')
    project_id = HiddenField("Project Id")
    submit = SubmitField("Grant Permission")
