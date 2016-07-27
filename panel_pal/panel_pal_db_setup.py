import sqlite3
import argparse
from db_commands import add_project, add_user

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
        CREATE TABLE pref_tx
            (id INTEGER PRIMARY KEY, project_id INTEGER, tx_id INTEGER, FOREIGN KEY(project_id) REFERENCES projects(id));
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
    if args.projects is not None:
        projects = args.projects.split(',')
        for project in projects:
            complete = add_project(project, conn_main)
            if not complete:
                print project + " not added to database"
    if args.users is not None:
        users = args.users.split(',')
        for user in users:
            complete = add_user(user, conn_main)
            if not complete:
                print user + " not added to database"


if __name__ == '__main__':
    main()
