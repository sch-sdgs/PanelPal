from flask_wtf import Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import TextField, SubmitField, HiddenField
from wtforms.validators import Required

from app.panel_pal import s
from app.models import *


class ProjectForm(Form):
    name = TextField("Project Name",  [Required("Enter a Project")])
    submit = SubmitField("Create Project")


def users():
    return s.query(Users)

class EditPermissions(Form):
    user_id  = QuerySelectField(query_factory=users,get_label='username')
    project_id = HiddenField("Project Id")
    submit = SubmitField("Grant Permission")
