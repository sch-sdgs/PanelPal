from app import db


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

    def __init__(self,name):
        self.name = name

    def __repr__(self):
        return '<name %r>' % (self.name)


class Panels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    current_version = db.Column(db.Integer)
    versions = db.relationship('Versions', backref='author', lazy='dynamic')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    def __init__(self, name, project_id, current_version):
        self.name = name
        self.project_id = project_id
        self.current_version = current_version

    def __repr__(self):
        return '<name %r>' % (self.name)


class PrefTx(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    def __init__(self, project_id, tx_id):
        self.project_id = project_id
        self.tx_id - tx_id

    def __repr__(self):
        return '<id %r>' % (self.id)


class VPRelationships(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    current_version = db.Column(db.Integer)
    version_id = db.Column(db.Integer, db.ForeignKey('versions.id'))
    vpanel_id = db.Column(db.Integer, db.ForeignKey('virtual_panels.id'))

    def __init__(self, name, current_version, version_id, vpanel_id):
        self.name = name
        self.current_version = current_version
        self.version_id = version_id
        self.panel_id = vpanel_id

    def __repr__(self):
        return '<name %r>' % (self.name)


class VirtualPanels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    current_version = db.Column(db.Integer)
    versions = db.relationship('VPRelationships', backref='author', lazy='dynamic')

    def __init__(self, name, current_version):
        self.name = name
        self.current_version = current_version

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

    def __init__(self, intro, last, panel_id, region_id, comment, extension_3, extension_5):
        self.intro = intro
        self.last = last
        self.panel_id = panel_id
        self.region_id = region_id
        self.comment = comment
        self.extension_3 = extension_3
        self.extension_5 = extension_5

    def __repr__(self):
        return '<id %r>' % (self.id)


class Genes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    tx = db.relationship('Tx', backref='y', lazy='dynamic')

    def __init__(self, name, tx):
        self.name = name
        self.tx = tx

    def __repr__(self):
        return '<name %r>' % (self.name)


class Tx(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accession = db.Column(db.String(30), unique=True)
    gene_id = db.Column(db.Integer, db.ForeignKey('genes.id'))
    strand = db.Column(db.String(1))
    exons = db.relationship('Exons', backref='z', lazy='dynamic')

    def __init__(self, accession, gene_id, strand, exons):
        self.accession = accession
        self.gene_id = gene_id
        self.strand = strand
        self.exons = exons

    def __repr__(self):
        return '<accession %r>' % (self.accession)


class Exons(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.Integer, db.ForeignKey('tx.id'))
    number = db.Column(db.Integer)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))

    def __init__(self, tx_id, number, region_id):
        self.tx_id = tx_id
        self.number = number
        self.region_id = region_id

    def __repr__(self):
        return '<id %r>' % (self.id)


class Regions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chrom = db.Column(db.String(4), primary_key=True)
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    name = db.Column(db.String(50))
    versions = db.relationship('Versions', backref='i', lazy='dynamic')
    exons = db.relationship('Exons', backref='i', lazy='dynamic')
    db.UniqueConstraint('chrom', 'start', 'end', name='_chrom_start_end')

    def __init__(self, chrom, start, end, name=None):
        self.chrom = chrom
        self.start = start
        self.end = end
        self.name = name

    def __repr__(self):
        return '<id %r>' % (self.id)
