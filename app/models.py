from panel_pal import db

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), index=False, unique=False)

    def __repr__(self):
        return '<Users %r>' % (self.username)