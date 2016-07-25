import sqlite3

def add_project(project, conn):
    pp = conn.cursor()
    try:
        pp.execute("INSERT OR IGNORE INTO projects(name) VALUES (?)", (project,))
        conn.commit()
        return True
    except conn.Error as e:
        conn.rollback()
        print e.args[0]
        return False

def add_user(user, conn):
    pp = conn.cursor()
    try:
        pp.execute("INSERT OR IGNORE INTO users(username) VALUES (?)", (user,))
        conn.commit()
        return True
    except conn.Error as e:
        conn.rollback()
        print e.args[0]
        return False

def additional_genes(genes, panel_id):
    return True


def import_bed(project, panel, gene_file, panel_pal, refflat):
    conn_panelpal = sqlite3.connect(panel_pal)
    pp = conn_panelpal.cursor()
    conn_refflat = sqlite3.connect(refflat)
    rf = conn_refflat.cursor()

    file = open(gene_file, 'r')
    genes = [line.strip('\n') for line in file.readlines()]

    pp.execute("SELECT * FROM panels WHERE name=?;", (panel,))
    row = pp.fetchone()

    if row eq None:
        for gene in genes:

    else:
        pp.execute("SELECT region_id FROM versions WHERE panel_id=?;", ())









