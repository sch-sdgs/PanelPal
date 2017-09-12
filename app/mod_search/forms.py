from flask_wtf import Form
from wtforms.fields import TextField, SubmitField, SelectField

class Search(Form):
    categories = [("Genes",'Gene'), ("Transcripts",'Transcript'), ("Panels",'Panel'), ("VPanels",'Virtual Panel'), ("Projects",'Project'), ("Users",'User')]
    search_term = TextField("Search term")
    tables = SelectField("Type", choices=categories)
    submit = SubmitField("Search")