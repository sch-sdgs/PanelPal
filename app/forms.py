from flask_wtf import FlaskForm
from wtforms.fields import TextField, SubmitField, HiddenField, PasswordField

# TODO is this needed?
# class UserForm(Form):
#     name = TextField("Username",  [Required("Enter a Username")])
#     admin = BooleanField("Admin")
#     submit = SubmitField("Send")
#
#
# class PrefTxCreate(Form):
#     gene = RadioField(u'Genes',choices=[],coerce=int)
#     project_id = TextField("Project ID")

class Login(FlaskForm):
    username  = TextField("Username")
    password = PasswordField("Password")
    submit = SubmitField("Login")
    next = HiddenField("Next")


