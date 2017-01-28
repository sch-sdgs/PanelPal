from app.queries import *
from sqlalchemy import and_, or_

from app.views import message
from app.mod_admin.queries import get_user_id_by_username
from app.models import *


@message
def create_preftx_entry(s, project_id):
    """
    DOSEN'T COMMIT DATA TO DB - to be used within another method that does.

    :param s:
    :param project_id:
    :return:
    """
    preftx = PrefTx(project_id=project_id, current_version=0)
    s.add(preftx)
    return preftx.id


@message
def create_project(s, name, user):
    project = Projects(name=name)
    s.add(project)
    s.flush()
    create_preftx_entry(s, project.id)
    user_id = get_user_id_by_username(s, user)
    user_rel = UserRelationships(user_id=user_id, project_id=project.id)
    s.add(user_rel)
    s.flush()
    s.commit()
    return project.id

def get_preftx_by_gene_id(s, project_id, gene_id):
    preftx = s.query(PrefTx,PrefTxVersions,Tx,Genes).\
        join(PrefTxVersions).\
        join(Tx).\
        join(Genes).\
        filter(and_(PrefTx.project_id == project_id,Genes.id == gene_id,or_(PrefTxVersions.last == PrefTx.current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro <= PrefTx.current_version)).values(PrefTxVersions.tx_id)
    for i in preftx:
        return i.tx_id


@message
def add_preftxs_to_panel(s, project_id, tx_ids):
    query = get_preftx_current_version(s, project_id)
    current_version = query[0]
    preftx_id = query[1]
    print preftx_id
    print "current_version:" + str(current_version)
    for i in tx_ids:
        tx_id = i["tx_id"]
        gene = i["gene"]
        gene_id = get_gene_id_from_name(s,gene)
        #get current preftx for that gene, if different then do the next bit
        stored_preftx = get_preftx_by_gene_id(s,project_id,gene_id)
        #todo this is not working
        if int(stored_preftx) != int(tx_id):
            print "hello hello"
            print preftx_id
            if preftx_id != 0:
                preftx = PrefTxVersions(s, pref_tx_id=preftx_id, tx_id=tx_id, intro=current_version + 1, last=None)
                s.add(preftx)
                s.flush()
    s.commit()

    return True

def get_upcoming_preftx_by_gene_id(s, project_id, gene_id):
    preftx = s.query(PrefTx,PrefTxVersions,Tx,Genes).\
        join(PrefTxVersions).\
        join(Tx).\
        join(Genes).\
        filter(and_(PrefTx.project_id == project_id,Genes.id == gene_id,or_(PrefTxVersions.last == PrefTx.current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro > PrefTx.current_version)).values(PrefTxVersions.tx_id)
    for i in preftx:
        return i.tx_id

def get_all_projects(s):
    """
    gets all projects, ids and names
    :param s: database session
    :return: sql alchemcy generator object
    """
    projects = s.query(Projects).values(Projects.id,Projects.name)
    return projects

def get_projects_by_user(s, username):
    user_id = get_user_id_by_username(s, username)
    projects = s.query(Projects, UserRelationships).join(UserRelationships).filter_by(user_id=user_id).values(
        Projects.id.label('id'), Projects.name.label('name'))
    print type(projects)
    return projects


def get_current_preftx_version(s,preftx_id):
    print "YO"
    print preftx_id
    query = s.query(PrefTx).filter(PrefTx.id == preftx_id).values(PrefTx.current_version)
    for i in query:
        return i.current_version

def get_preftx_id_by_project_id(s, project_id):
    query = s.query(PrefTx).filter(PrefTx.project_id == project_id).values(PrefTx.id)
    for i in query:
        return i.id

def check_preftx_status_query(s, id):
    """
    query to check the status of a virtual panel - returns fields required to decide status of a panel

    :param s: db session
    :param id: panel id
    :return: result of query
    """

    panels = s.query(PrefTx, PrefTxVersions).filter(PrefTx.id == id).join(PrefTxVersions). \
        values(PrefTx.current_version, \
               PrefTxVersions.last, \
               PrefTxVersions.intro)

    return panels


def get_preftx_current_version(s, project_id):
    version = s.query(PrefTx).filter(PrefTx.project_id == project_id).values(PrefTx.current_version, PrefTx.id)
    for i in version:
        return [i.current_version, i.id]

def get_project_id_by_preftx_id(s, preftx_id):
    project = s.query(PrefTx).filter(PrefTx.id == preftx_id).values(PrefTx.project_id)
    print "ME"
    print preftx_id
    for i in project:
        return i.project_id


@message
def make_preftx_live(s, preftx_id, new_version, username):
    """
    makes a panel line

    :return: True
    :param s: db session
    :param panelid: panel id
    :param new_version: the new version number of the panel
    """
    project_id = get_project_id_by_preftx_id(s, preftx_id)
    print "BOOM"
    print project_id
    if check_user_has_permission(s, username, project_id):
        print "MAKING LIVE"
        s.query(PrefTx).filter_by(id=preftx_id).update({PrefTx.current_version: new_version})
        s.commit()
        return True
    else:
        return False

def get_preftx_by_project_id(s, id):
    """
    gets pref transcripts by project id - only gets transcripts in the current version

    :param s: db session
    :param id: project id
    :return: sql alchemy object
    """

    preftx = s.query(Genes, Tx, PrefTxVersions, PrefTx, Projects). \
        filter(and_(PrefTx.project_id == id, \
                    or_(PrefTxVersions.last >= PrefTx.current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro <= PrefTx.current_version)). \
        join(Tx). \
        join(PrefTxVersions). \
        join(PrefTx). \
        join(Projects). \
        values(Projects.id, \
               Projects.name.label("projectname"), \
               Genes.name.label("genename"), \
               Tx.accession, \
               Tx.tx_start, \
               Tx.tx_end, \
               Tx.strand, \
               PrefTx.id.label("preftx_id"),
               PrefTxVersions.intro, \
               PrefTxVersions.last, \
               PrefTx.current_version)

    return preftx


def get_changes_preftx_by_project_id(s, id):
    """
    gets changes to pf transcripts that are not yet live by project id

    :param s: db session
    :param id: project id
    :return: sql alchemy object
    """

    preftx = s.query(Genes, Tx, PrefTxVersions, PrefTx, Projects). \
        filter(and_(PrefTx.project_id == id, \
                    or_(PrefTxVersions.last == PrefTx.current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro <= PrefTx.current_version)). \
        join(Tx). \
        join(PrefTxVersions). \
        join(PrefTx). \
        join(Projects). \
        values(Projects.id, \
               Projects.name.label("projectname"), \
               Genes.name.label("genename"), \
               Tx.accession, \
               Tx.tx_start, \
               Tx.tx_end, \
               Tx.strand)

    return preftx

def get_project_name(s, projectid):
    """
    gets project name by project id

    :param s: db session
    :param id: project id
    :return: sql alchemy object
    """
    name = s.query(Projects).filter_by(id=projectid)
    for i in name:
        return i.name

@message
def add_user_project_rel(s, user_id, project_id):
    check = s.query(UserRelationships).filter(
        and_(UserRelationships.user_id == user_id, UserRelationships.project_id == project_id)).count()
    print check
    if check == 0:
        rel = UserRelationships(user_id=user_id, project_id=project_id)
        s.add(rel)
        s.commit()
    return True

@message
def remove_user_project_rel(s,rel_id):
    s.query(UserRelationships).filter_by(id=rel_id).delete()
    s.commit()
    return True

@message
def remove_user_project_rel_no_id(s,username,project_id):
    user_id = get_user_id_by_username(s,username)
    rels = s.query(Projects, UserRelationships, Users). \
        distinct(Users.username). \
        group_by(Users.username). \
        join(UserRelationships). \
        join(Users). \
        filter(and_(UserRelationships.project_id == project_id,Users.id==user_id)).values(
                                                                  UserRelationships.id.label("rel_id"),
                                                                  )
    for i in rels:
        s.query(UserRelationships).filter_by(id=i.rel_id).delete()
        s.commit()
        return True

def get_user_rel_by_project_id(s, project_id):
    rels = s.query(Projects, UserRelationships, Users). \
        distinct(Users.username). \
        group_by(Users.username). \
        join(UserRelationships). \
        join(Users). \
        filter(UserRelationships.project_id == project_id).values(Users.username, Projects.name,
                                                                  UserRelationships.id.label("rel_id"),
                                                                  UserRelationships.project_id.label("project_id"),
                                                                  UserRelationships.user_id.label("user_id"))
    return rels

def get_project_id_by_name(s,name):
    project = s.query(Projects).filter(Projects.name == name).values(Projects.id)
    for i in project:
        return i.id

