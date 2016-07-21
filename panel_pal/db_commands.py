import sqlite3
import argparse
import json

def create_db(conn):
    pp = conn.cursor()
    pp.executescript('drop table if exists projects;')
    pp.executescript('drop table if exists panels;')
    pp.executescript('drop table if exists versions;')
    pp.executescript('drop table if exists users;')
    pp.executescript('drop table if exists ref_logtable;')

    try:
        pp.executescript("begin")
        pp.executescript("""
        CREATE TABLE projects
            (id INTEGER PRIMARY KEY, name VARCHAR(50), UNIQUE(name));
        CREATE TABLE panels
            (id INTEGER PRIMARY KEY, name VARCHAR(50), team_id INTEGER, current_version INTEGER, FOREIGN KEY(team_id) REFERENCES projects(id), UNIQUE(name));
        CREATE TABLE versions
            (id INTEGER PRIMARY KEY, intro INTEGER, last INTEGER, panel_id INTEGER, region_id INTEGER, comment VARCHAR(100), extension_3 INTEGER, extension_5 INTEGER, FOREIGN KEY(panel_id) REFERENCES panels(id));
        CREATE TABLE users
            (id INTEGER PRIMARY KEY, username varchar(20), UNIQUE(username));
        CREATE TABLE ref_logtable
            (id INTEGER PRIMARY KEY, project_id INTEGER, version_id INTEGER, region_id INTEGER, user_id INTEGER, FOREIGN KEY(project_id) REFERENCES projects(id), FOREIGN KEY(version_id) REFERENCES versions(id), FOREIGN KEY(user_id) REFERENCES users(id));
        """)
        pp.executescript("commit")
        return True
    except conn.Error as e:
        pp.executescript("rollback")
        print e.args[0]
        return False

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

def query_db(c, query, args=(), one=False):
    """

    general method to do a select statement and format result into an easy to use dict

    :param c:
    :param query:
    :param args:
    :param one:
    :return: list of dicts
    """
    c.execute(query, args)
    r = [dict((c.description[i][0], value) \
               for i, value in enumerate(row)) for row in c.fetchall()]
    return (r[0] if r else None) if one else r

class regions():

    def get_regions_by_gene(self,gene):
        db = 'resources/refflat.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()
        result = query_db(c,"SELECT * FROM genes join tx on genes.id=tx.gene_id join exons on tx.id = exons.tx_id WHERE name=?", (gene,))
        formatted_result = {}
        formatted_result[gene] = {}
        for region in result:
            tx = region["accession"]
            exon_id = region["id"]
            number = region["number"]
            chrom = region["chrom"]
            strand = region["strand"]
            start = region["start"]
            end = region["end"]
            formatted_result[gene]["chrom"]=chrom
            if tx not in formatted_result[gene]:
                formatted_result[gene][tx]={}
            formatted_result[gene][tx]["strand"] = strand
            if "exons" not in formatted_result[gene][tx]:
                formatted_result[gene][tx]["exons"]=[]
                exon_details = {"id": exon_id, "start": start, "end": end, "number": number}
            formatted_result[gene][tx]["exons"].append(exon_details)

        return formatted_result

    def get_regions_by_tx(self, tx):
        db = 'resources/refflat.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()
        result = query_db(c,
                          "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE accession=?",
                          (tx,))
        formatted_result = {}
        formatted_result[tx] = {}
        for region in result:
            name = region["name"]
            tx = region["accession"]
            exon_id = region["id"]
            chrom = region["chrom"]
            strand = region["strand"]
            start = region["start"]
            end = region["end"]
            number = region["number"]
            formatted_result[tx]["chrom"] = chrom
            formatted_result[tx]["gene"] = name
            formatted_result[tx]["strand"] = strand
            if "exons" not in formatted_result[tx]:
                formatted_result[tx]["exons"] = []
            exon_details = {"id": exon_id, "start": start, "end": end, "number":number}
            formatted_result[tx]["exons"].append(exon_details)



        return formatted_result

    def genes_in_region(self,chrom,start,end):
        # TODO will only get if exon is in region need to do introns too
        db = 'resources/refflat.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()
        fully_within = query_db(c,
                          "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE chrom=? AND (start >= ? AND end <= ?)",
                          (chrom,start,end,))
        x = query_db(c,
                                "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE chrom=? AND (start <= ? AND end >= ?)",
                                (chrom, start,start,))
        y = query_db(c,
                                "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE chrom=? AND (start <= ? AND end >=  ?)",
                                (chrom, end,end,))

        c.connection.close()

        return fully_within + x + y



r=regions()
print json.dumps(r.genes_in_region('chr17',7589542,7589388),indent=4)


def main():
    parser = argparse.ArgumentParser(description='creates db tables required for PanelPal program')
    parser.add_argument('--db', default="resources/")
    parser.add_argument('--projects', default="CTD,IEM,Haems,HeredCancer,DevDel,NGD")
    parser.add_argument('--users')
    args = parser.parse_args()

    db = args.db + 'panel_pal.db'

    conn_main = sqlite3.connect(db)

    complete = create_db(conn_main)

    if not complete:
        print "Database creation failed. Exiting."
        exit()

    projects = args.projects.split(',')
    for project in projects:
        complete = add_project(project, conn_main)
        if not complete:
            print project + " not added to database"

    users = args.users.split(',')
    for user in users:
        complete = add_user(user, conn_main)
        if not complete:
            print user + " not added to database"


if __name__ == '__main__':
    main()
