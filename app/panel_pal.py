from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import logging
from logging.handlers import TimedRotatingFileHandler
import inspect
import itertools
from functools import wraps
from flask_login import current_user

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = 'development key'
db = SQLAlchemy(app)

session_factory = sessionmaker(bind=db)
session = scoped_session(session_factory)
s = db.session

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

handler = TimedRotatingFileHandler('/tmp/PanelPal.log', when="d", interval=1, backupCount=30)
handler.setLevel(logging.INFO)

def message(f):
    """
    decorator that allows query methods to log their actions to a log file so that we can track users

    :param f:
    :return:
    """
    @wraps(f)
    def decorated_function(*args,**kwargs):
        method = f.__name__

        formatter = logging.Formatter('%(levelname)s|' + current_user.id + '|%(asctime)s|%(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

        args_name = inspect.getargspec(f)[0]
        args_dict = dict(itertools.izip(args_name, args))

        del args_dict['s']
        app.logger.info(method + "|" + str(args_dict))
        return f(*args, **kwargs)
    return decorated_function



from mod_projects.views import projects
from mod_panels.views import panels
from mod_admin.views import admin
from mod_api.views import api_blueprint
from mod_search.views import search


from app.views import *



app.register_blueprint(admin,url_prefix='/admin')
app.register_blueprint(api_blueprint,url_prefix='/api')
app.register_blueprint(projects,url_prefix='/projects')
app.register_blueprint(panels,url_prefix='/panels')
app.register_blueprint(search,url_prefix='/search')




