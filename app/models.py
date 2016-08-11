from panel_pal import db


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=False)

    def __repr__(self):
        return '<Users %r>' % (self.username)


class Projects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    panels = db.relationship('Panels', backref='author', lazy='dynamic')
    pref_tx = db.relationship('PrefTx', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<name %r>' % (self.name)


class PrefTx(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    def __repr__(self):
        return '<id %r>' % (self.id)


class Panels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    current_version = db.Column(db.Integer)
    name = db.Column(db.String(50))
    versions = db.relationship('Versions', backref='x', lazy='dynamic')

    def __repr__(self):
        return '<name %r>' % (self.name)


class Versions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intro = db.Column(db.Integer)
    last = db.Column(db.Integer)
    comment = db.Column(db.String(100))
    extension_3 = db.Column(db.Integer)
    extension_5 = db.Column(db.Integer)

    panel_id = db.Column(db.Integer, db.ForeignKey('panels.id'))
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))

    def __repr__(self):
        return '<id %r>' % (self.id)


class Genes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    tx = db.relationship('Tx', backref='y', lazy='dynamic')


class Tx(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accession = db.Column(db.String(30), unique=True)
    gene_id = db.Column(db.Integer, db.ForeignKey('genes.id'))
    strand = db.Column(db.String(1))
    exons = db.relationship('Exons', backref='z', lazy='dynamic')


class Exons(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.Integer, db.ForeignKey('tx.id'))
    number = db.Column(db.Integer)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))


class Regions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chrom = db.Column(db.String(4), primary_key=True)
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    versions = db.relationship('Versions', backref='i', lazy='dynamic')
    exons = db.relationship('Exons', backref='i', lazy='dynamic')
    db.UniqueConstraint('chrom', 'start', 'end', name='_chrom_start_end')
