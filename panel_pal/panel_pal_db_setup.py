import sqlite3
import argparse
from db_commands import Projects, Users, Panels
import parse_refflat_into_db
import os

def create_db(conn):
    pp = conn.cursor()
    pp.executescript('drop table if exists projects;')
    pp.executescript('drop table if exists panels;')
    pp.executescript('drop table if exists versions;')
    pp.executescript('drop table if exists VP_relationships')
    pp.executescript('drop table if exists virtual_panels')
    pp.executescript('drop table if exists pref_tx;')
    pp.executescript('drop table if exists pref_tx_versions')
    pp.executescript('drop table if exists users;')
    pp.executescript('drop table if exists user_relationships;')
    pp.executescript('drop table if exists ref_logtable;')

    try:
        pp.executescript("begin")
        pp.executescript("""
        CREATE TABLE projects
            (id INTEGER PRIMARY KEY, name VARCHAR(50), UNIQUE(name));
        CREATE TABLE panels
            (id INTEGER PRIMARY KEY, project_id INTEGER, name VARCHAR(50), locked INTEGER, current_version INTEGER, FOREIGN KEY(locked) REFERENCES users(id), FOREIGN KEY(project_id) REFERENCES projects(id), UNIQUE(name));
        CREATE TABLE versions
            (id INTEGER PRIMARY KEY, intro INTEGER, last INTEGER, panel_id INTEGER, region_id INTEGER, comment VARCHAR(100), extension_3 INTEGER, extension_5 INTEGER, FOREIGN KEY(panel_id) REFERENCES panels(id), FOREIGN KEY(region_id) REFERENCES regions(id));
        CREATE TABLE VP_relationships
            (id INTEGER PRIMARY KEY, intro INTEGER, last INTEGER, version_id INTEGER, vpanel_id INTEGER, FOREIGN KEY(version_id) REFERENCES versions(id), FOREIGN KEY(vpanel_id) REFERENCES virtual_panels(id));
        CREATE TABLE virtual_panels
            (id INTEGER PRIMARY KEY, name VARCHAR(50), current_version INTEGER, UNIQUE(name));
        CREATE TABLE pref_tx
            (id INTEGER PRIMARY KEY, project_id INTEGER, current_version INTEGER, FOREIGN KEY(project_id) REFERENCES projects(id));
        CREATE TABLE pref_tx_versions
            (id INTEGER PRIMARY KEY, pref_tx_id INTEGER, tx_id INTEGER, intro INTEGER, last INTEGER, FOREIGN KEY(pref_tx_id) REFERENCES pref_tx(id), FOREIGN KEY(tx_id) REFERENCES tx(id));
        CREATE TABLE users
            (id INTEGER PRIMARY KEY, username varchar(20), admin INTEGER,  UNIQUE(username));
        CREATE TABLE user_relationships
            (id INTEGER PRIMARY KEY, user_id INTEGER, project_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(project_id) REFERENCES projects(id));
        CREATE TABLE ref_logtable
            (id INTEGER PRIMARY KEY, project_id INTEGER, version_id INTEGER, region_id INTEGER, user_id INTEGER, FOREIGN KEY(project_id) REFERENCES projects(id), FOREIGN KEY(version_id) REFERENCES versions(id), FOREIGN KEY(user_id) REFERENCES users(id));
        """)
        pp.executescript("commit")
        return True
    except conn.Error as e:
        pp.executescript("rollback")
        print(e.args[0])
        return False

def main():
    p=Projects()
    u=Users()
    pan=Panels()

    parser = argparse.ArgumentParser(description='creates db tables required for PanelPal program')
    parser.add_argument('--db')
    parser.add_argument('--projects', default="CTD,IEM,Haems,HeredCancer,DevDel,NGD,Research")
    parser.add_argument('--studies', default="CTD,IEM,Haems_Bleeding,Haems_BMF,Haems_TruSight,HeredCancer_TruSight,HeredCancer_SureSelect,DevDel,NGD,NGD_Motor,NGD_Movement")
    parser.add_argument('--users', default='dnamdp,cytng,gencph,genes,dnanhc')
    args = parser.parse_args()


    db = '/home/bioinfo/Natalie/wc/panel_pal/resources/panel_pal.db'
    print(db)

    conn_main = sqlite3.connect(db)

    parse_refflat_into_db.main(db)
    complete = create_db(conn_main)

    if not complete:
        print "Database creation failed. Exiting."
        exit()
    if args.projects is not None:
        projects = args.projects.split(',')
        for project in projects:
            complete = p.add_project(project)
            if complete == -1:
                print project + " not added to database"
    if args.studies is not None:
        studies = args.studies.split(',')
        for study in studies:
            if '_' in study:
                project = study.split('_')[0]
            else:
                project = study
            project_id = p.get_project(project)
            if project_id == -1:
                print project + " is not a project; cannot add " + study
            else:
                complete = pan.add_panel(study,project_id)
                if complete == -1:
                    print study + " not added to database"
    if args.users is not None:
        users = args.users.split(',')
        for user in users:
            complete = u.add_user(user, 1)
            if complete == -1:
                print user + " not added to database"


if __name__ == '__main__':
    main()
