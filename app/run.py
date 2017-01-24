#!flask/bin/python
from app.main import app
from flask_bootstrap import Bootstrap
Bootstrap(app)
app.run(debug=True,host= '10.182.131.21',port=5008)