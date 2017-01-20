import os
basedir = os.path.dirname(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + basedir + '/resources/panel_pal.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
print SQLALCHEMY_DATABASE_URI
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'resources')