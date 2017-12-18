#!flask/bin/python
from app.panel_pal import app
from flask_bootstrap import Bootstrap
Bootstrap(app)
from flask_jsglue import JSGlue
jsglue = JSGlue(app)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)
