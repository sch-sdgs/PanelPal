from sqlalchemy import and_, or_, desc, func, case, cast, String, text, exc
from flask.ext.login import current_user
from app.models import *
from functools import wraps
import logging
from logging.handlers import TimedRotatingFileHandler
from app.main import app
import inspect
import itertools

handler = TimedRotatingFileHandler('PanelPal.log', when="d",interval=1,backupCount=30)
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


def get_virtual_panels_simple(s):
    vpanels = s.query(VirtualPanels, VPRelationships, Versions, Panels). \
        group_by(VirtualPanels.name). \
        join(VPRelationships). \
        join(Versions). \
        join(Panels). \
        values(VirtualPanels.current_version, \
               VirtualPanels.name.label('vp_name'), \
               VirtualPanels.id,
               Panels.id.label('panelid'),
               Panels.locked,
               Panels.project_id.label('projectid'))

    return vpanels


def get_virtual_panels(s):
    """
    gets all virtual panels
    :param s: database session (initiated on app run)
    :return: sql alchemy object
    """

    vpanels = s.query(VirtualPanels, VPRelationships, Versions, Panels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        values(VirtualPanels.current_version, \
               VirtualPanels.id.label("virtualpanlelid"), \
               VirtualPanels.name.label("virtualpanelname"), \
               Panels.name.label("panelname"))

    return vpanels


def get_panels(s):
    """
    gets all panels in database
    :param s: database session (initiated on app run)
    :return: sql alchemy object with study name and study id
    """
    panels = s.query(Projects, Panels).join(Panels). \
        values(Panels.name.label("panelname"), \
               Panels.current_version, \
               Panels.id.label("panelid"), \
               Projects.name.label("projectname"), \
               Projects.id.label("projectid"),
               Panels.locked)

    return panels

def get_panel_by_vp_id(s, vp_id):
    panel = s.query(VirtualPanels, VPRelationships, Versions).join(VPRelationships).join(Versions).distinct(Versions.panel_id).group_by(Versions.panel_id).filter(VirtualPanels.id==vp_id).values(Versions.panel_id)
    for i in panel:
        return i.panel_id


def get_virtual_panels_by_panel_id(s, id):
    vpanels = s.query(VirtualPanels, VPRelationships, Versions, Panels, Projects). \
        distinct(VirtualPanels.name). \
        group_by(VirtualPanels.name). \
        join(VPRelationships). \
        join(Versions). \
        join(Panels). \
        join(Projects). \
        filter(Panels.id == id). \
        values(VirtualPanels.id, \
               VirtualPanels.current_version, \
               Panels.name.label('panelname'),
               Panels.id.label('panelid'),
               Projects.id.label('projectid'),
               Panels.locked,
               VirtualPanels.name.label('vp_name'))
    return vpanels


def get_panels_by_project_id(s, id):
    """
    gets panels by project id

    :param s: db session
    :param id: project id
    :return: sql alchemy object
    """
    panels = s.query(Projects, Panels). \
        join(Panels). \
        filter_by(project_id=id). \
        values(Projects.id.label("projectid"), \
               Projects.name.label("projectname"), \
               Panels.name.label("panelname"), \
               Panels.current_version, \
               Panels.id.label("panelid"), \
               Panels.locked)

    return panels


def check_panel_status_query(s, id):
    """
    query to check the status of a panel - returns fields required to decide status of a panel

    :param s: db session
    :param id: panel id
    :return: result of query
    """
    panels = s.query(Panels, Versions).filter_by(id=id).join(Versions). \
        values(Panels.name, \
               Panels.current_version, \
               Versions.last, \
               Versions.intro)
    return panels


def check_virtualpanel_status_query(s, id):
    """
    query to check the status of a virtual panel - returns fields required to decide status of a panel

    :param s: db session
    :param id: panel id
    :return: result of query
    """

    panels = s.query(VirtualPanels, VPRelationships).filter_by(id=id).join(VPRelationships). \
        values(VirtualPanels.name, \
               VirtualPanels.current_version, \
               VPRelationships.last, \
               VPRelationships.intro)

    return panels


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
# todo do we need start filter here
def get_panel_edit(s, id, version):
    """
    gets a version of a panel

    :param s: db session
    :param id: panelid
    :param version: version required
    :return: sql alchemy objct
    """
    query = s.query(Panels, Versions, Genes, Tx, Exons, Regions). \
        filter(Panels.id == id, \
               or_(Versions.last > version, \
                   Versions.last == None)). \
        order_by(desc(Regions.start)). \
        join(Versions). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        join(Genes).values(Panels.id.label("panelid"), \
                           Panels.current_version, \
                           Panels.name.label("panelname"), \
                           Versions.intro, \
                           Versions.last, \
                           Versions.region_id, \
                           Versions.id, \
                           Versions.extension_3, \
                           Versions.extension_5, \
                           Genes.name.label("genename"), \
                           Regions.chrom, \
                           Regions.start, \
                           Regions.end, \
                           Exons.number, \
                           Tx.accession)

    return query


def get_current_version(s, panelid):
    """
    gets current version of a panel given the panel id

    :param s: db session
    :param panelid: panel id
    :return: the panel id
    """
    version = s.query(Panels).filter_by(id=panelid).values(Panels.current_version)
    for i in version:
        return i.current_version

def get_current_vpanel_version(s, vpanelid):
    """
    gets current version of a panel given the panel id

    :param s: db session
    :param panelid: panel id
    :return: the panel id
    """
    version = s.query(VirtualPanels).filter_by(id=vpanelid).values(VirtualPanels.current_version)
    for i in version:
        return i.current_version

def get_current_version_vp(s, panelid):
    """
    gets current version of a panel given the panel id

    :param s: db session
    :param panelid: panel id
    :return: the panel id
    """
    version = s.query(VirtualPanels).filter_by(id=panelid).values(VirtualPanels.current_version)
    for i in version:
        return i.current_version


def get_current_vp_version(s, panelid):
    """
    gets current version of a panel given the panel id

    :param s: db session
    :param panelid: panel id
    :return: the panel id
    """
    version = s.query(VirtualPanels).filter_by(id=panelid).values(VirtualPanels.current_version)
    for i in version:
        return i.current_version

@message
def create_panel_query(s, projectid, name):
    """
    creates an entry in the panels table ready for regions(versions) to be added

    :param s: db session
    :param projectid: project id
    :param name: panel name
    :return: panel id
    """
    panel = Panels(name, int(projectid), 0, None)
    s.add(panel)
    s.commit()
    return panel.id

@message
def create_virtualpanel_query(s, name):
    """
    creates a virtual panel in the virtual panels table and adds the vp_relationship to the broad panel

    :param s: db session
    :param name: name of virtual panel
    :return: virtual panel id
    """
    try:
        virtualpanel = VirtualPanels(name, 0)
        s.add(virtualpanel)
        s.commit()
        return virtualpanel.id
    except exc.IntegrityError:
        return -1

@message
def remove_virtualpanel_query(s, name):
    """

    :param s:
    :param name:
    :return:
    """
    s.query(VirtualPanels).filter_by(name=name).delete()
    s.commit()
    return True

@message
def add_region_to_panel(s, regionid, panelid):
    """
    called by other query method - this method DOES NOT COMMIT CHANGES TO THE DATABASE
    THIS METHOD MUST BE USED WITH OTHER METHODS

    :param s: db sessoin
    :param regionid: region id
    :param panelid: panel id
    :return: the id in the versions table
    """
    current = get_current_version(s, panelid)

    version = Versions(intro=int(current) + 1, last=None, panel_id=panelid, region_id=regionid, comment=None,
                       extension_3=None, extension_5=None)
    s.add(version)
    # s.commit()
    return version.id

@message
def add_genes_to_panel(s, panelid, gene):
    """
    given a gene and a panelid this query gets all the regions for the gene and calls add_region_to_panel to add them
    :param s: db session
    :param panelid: the panel id
    :param gene: the gene
    """

    query = s.query(Genes, Tx, Exons, Regions). \
        filter(Genes.name == gene). \
        join(Tx). \
        join(Exons). \
        join(Regions).values(Regions.id)
    # adds them to the panel
    for i in query:
        add_region_to_panel(s, i.id, panelid)
    s.commit()

@message
def add_version_to_vp(s, vp_id, version_id):
    """

    :param s:
    :param vp_id:
    :param version_id:
    :return:
    """
    vp_relationship = VPRelationships(intro=1, last=None, version_id=version_id, vpanel_id=vp_id)
    s.add(vp_relationship)
    s.commit()
    return vp_relationship.id

@message
def make_panel_live(s, panelid, new_version, username):
    """
    makes a panel line

    :return: True
    :param s: db session
    :param panelid: panel id
    :param new_version: the new version number of the panel
    """
    project_id = get_project_id_by_panel_id(s, panelid)
    if check_user_has_permission(s, username, project_id):
        s.query(Panels).filter_by(id=panelid).update({Panels.current_version: new_version})
        s.commit()
        return True
    else:
        return False

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


def get_project_id_by_panel_id(s, panelid):
    project = s.query(Projects, Panels).join(Panels).filter(Panels.id == panelid).values(Projects.id)
    for i in project:
        return i.id

def get_project_id_by_preftx_id(s, preftx_id):
    project = s.query(PrefTx).filter(PrefTx.id == preftx_id).values(PrefTx.project_id)
    print "ME"
    print preftx_id
    for i in project:
        return i.project_id

@message
def make_vp_panel_live(s, panelid, new_version):
    """
    makes a panel line

    :return: True
    :param s: db session
    :param panelid: panel id
    :param new_version: the new version number of the panel
    """
    s.query(VirtualPanels).filter_by(id=panelid).update({VirtualPanels.current_version: new_version})
    s.commit()

    return True


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


def get_genes_by_projectid(s, projectid):
    """
    gets transcripts by project id

    :param s: db session
    :param id: project id
    :return: sql alchemy object
    """
    genes = s.query(Genes, Tx, Exons, Regions, Versions, Panels, Projects). \
        distinct(Tx.accession). \
        group_by(Tx.accession). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(Panels). \
        join(Projects). \
        filter_by(id=projectid). \
        values(Tx.id.label("txid"), \
               Projects.name.label("projectname"), \
               Projects.id.label("projectid"), \
               Genes.name.label("genename"), \
               Genes.id.label("geneid"), \
               Tx.accession, \
               Tx.tx_start, \
               Tx.tx_end, \
               Tx.strand)
    return genes

def get_genes_by_projectid_new(s, projectid):
    """
    gets transcripts by project id

    :param s: db session
    :param id: project id
    :return: sql alchemy object
    """
    print projectid
    genes = s.query(Genes, Tx, PrefTxVersions, PrefTx, Projects). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        join(Tx). \
        join(PrefTxVersions). \
        join(PrefTx). \
        join(Projects). \
        filter(Projects.id==projectid). \
        values(Tx.id.label("txid"), \
               Projects.name.label("projectname"), \
               Projects.id.label("projectid"), \
               Genes.name.label("genename"), \
               Genes.id.label("geneid"), \
               Tx.accession, \
               Tx.tx_start, \
               Tx.tx_end, \
               Tx.strand)
    return genes

def get_genes_by_panelid(s, panelid, current_version):
    genes = s.query(Genes, Tx, Exons, Regions, Versions, Panels). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(Panels). \
        filter(and_(Panels.id == panelid, Versions.intro <= current_version, or_(Versions.last >= current_version, Versions.last == None))). \
        values(Genes.name, \
               Genes.id)
    return genes

def get_genes_by_vpanelid(s, vpanel_id, current_version):
    genes = s.query(Genes, Tx, Exons, Regions, Versions, VPRelationships, VirtualPanels). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(and_(VirtualPanels.id == vpanel_id, VPRelationships.intro <= current_version, or_(VPRelationships.last >= current_version, VPRelationships.last == None))). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        values(Genes.name, Genes.id)

    return genes

def get_gene_from_tx(s,tx_id):
    genes = s.query(Tx, Genes). \
        join(Genes). \
        filter(Tx.id == tx_id). \
        values(Genes.name, Genes.id)
    return genes

def get_regions_by_geneid(s, geneid, panelid):
    """
    gets current regions for a given gene within a given panel

    :param s:
    :param geneid:
    :param panelid:
    :return:
    """
    current_version = get_current_version(s, panelid)

    sql = text("""SELECT versions.id AS version_id,
                    regions.chrom,
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start ELSE regions.start + versions.extension_5 END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" ELSE regions."end" + versions.extension_3 END AS region_end,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM panels, versions
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = :panel_id AND genes.id = :gene_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL)
                    GROUP BY regions.id ORDER BY region_start""")
    values = {'panel_id':panelid, 'gene_id':geneid, 'version':current_version}
    regions = s.execute(sql, values)
    return regions

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


def get_preftx_current_version(s, project_id):
    version = s.query(PrefTx).filter(PrefTx.project_id == project_id).values(PrefTx.current_version, PrefTx.id)
    for i in version:
        return [i.current_version, i.id]

def get_gene_id_from_name(s,gene_name):
    gene = s.query(Genes).filter(Genes.name == gene_name).values(Genes.id)
    for i in gene:
        return i.id

def get_tx_id_from_name(s,tx_name):
    trans = s.query(Tx).filter(Tx.accession == tx_name).values(Tx.id)
    for i in trans:
        return i.id

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


def get_user_id_by_username(s, username):
    user = s.query(Users).filter_by(username=username).values(Users.username, Users.id)
    for i in user:
        return i.id


def get_user_by_username(s, username):
    user = s.query(Users).filter_by(username=username)
    return user


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

def get_projects_by_user(s, username):
    user_id = get_user_id_by_username(s, username)
    projects = s.query(Projects, UserRelationships).join(UserRelationships).filter_by(user_id=user_id).values(
        Projects.id.label('id'), Projects.name.label('name'))
    print type(projects)
    return projects


def check_user_has_permission(s, username, project_id):
    if username == "":
        return True
    check = s.query(Users, UserRelationships).join(UserRelationships).filter(
        and_(Users.username == username, UserRelationships.project_id == project_id)).count()
    print check
    if check == 0:
        return False
    else:
        return True

@message
def lock_panel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: user_id})
    s.commit()
    return True

@message
def unlock_panel_query(s, panel_id):
    unlock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: None})
    s.commit()
    return True


def get_username_by_user_id(s, user_id):
    username = s.query(Users).filter_by(id=user_id).values(Users.username)
    for i in username:
        return i.username


class PanelApiReturn(object):
    def __init__(self, current_version, result):
        self.current_version = current_version
        self.result = result


def get_panel_api(s, panel_name, version='current'):
    panel_ids = s.query(Panels).filter_by(name=panel_name).values(Panels.id)
    for i in panel_ids:
        panel_id = i.id
    if version == "current":
        current_version = get_current_version(s, panel_id)
    else:
        current_version = version
    panel = s.query(Panels, Versions, Regions, Exons, Tx, Genes). \
        join(Versions). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        join(Genes). \
        filter(and_(Panels.id == panel_id, Versions.intro <= current_version,
                    or_(Versions.last >= current_version, Versions.last == None))).order_by(Regions.start)
    return PanelApiReturn(current_version, panel)


def get_vpanel_api(s, panel_name, version='current'):
    panel_ids = s.query(VirtualPanels).filter_by(name=panel_name).values(VirtualPanels.id)
    for i in panel_ids:
        panel_id = i.id
    if version == "current":
        current_version = get_current_version_vp(s, panel_id)
    else:
        current_version = version
    panel = s.query(VirtualPanels, VPRelationships, Versions, Regions, Exons, Tx, Genes). \
        join(VPRelationships). \
        join(Versions). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        join(Genes). \
        filter(and_(VirtualPanels.id == panel_id, VPRelationships.intro <= current_version,
                    or_(VPRelationships.last >= current_version, VPRelationships.last == None))).order_by(Regions.start)
    return PanelApiReturn(current_version, panel)


def get_exonic_api(s, panel_name, version='current'):
    panel_ids = s.query(VirtualPanels).filter_by(name=panel_name).values(VirtualPanels.id)
    for i in panel_ids:
        panel_id = i.id
    if version == "current":
        current_version = get_current_version_vp(s, panel_id)
    else:
        current_version = version
    panel = s.query(VirtualPanels, VPRelationships, Versions, Regions, Exons, Tx, Genes). \
        join(VPRelationships). \
        join(Versions). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        join(Genes). \
        filter(and_(VirtualPanels.id == panel_id, VPRelationships.intro <= current_version,
                    or_(VPRelationships.last >= current_version, VPRelationships.last == None))).order_by(
        Regions.start).values()
    return PanelApiReturn(current_version, panel)

def get_project_id_by_name(s,name):
    project = s.query(Projects).filter(Projects.name == name).values(Projects.id)
    for i in project:
        return i.id

def get_current_preftx_version(s,preftx_id):
    print "YO"
    print preftx_id
    query = s.query(PrefTx).filter(PrefTx.id == preftx_id).values(PrefTx.current_version)
    for i in query:
        return i.current_version

def get_preftx_id_by_project_id(s,project_id):
    query = s.query(PrefTx).filter(PrefTx.project_id == project_id).values(PrefTx.id)
    for i in query:
        return i.id

def get_preftx_api(s,project_name,version='current'):
    print "HELLO HERE"
    project_id = get_project_id_by_name(s,project_name)
    preftx_id = get_preftx_id_by_project_id(s, project_id)
    print project_id
    if version == "current":
        current_version = get_current_preftx_version(s, preftx_id)
    else:
        current_version = version

    print current_version
    preftx = s.query(Genes, Tx, PrefTxVersions, PrefTx, Projects). \
        filter(and_(PrefTx.project_id == project_id, \
                    or_(PrefTxVersions.last >= current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro <= current_version)). \
        join(Tx). \
        join(PrefTxVersions). \
        join(PrefTx). \
        join(Projects). \
        values(PrefTx.current_version,
               Tx.accession)

    return PanelApiReturn(current_version, preftx)

def get_panel_by_vpanel_id(s, vp_id):
    panel = s.query(Panels, Versions, VPRelationships, VirtualPanels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(VirtualPanels.id == vp_id). \
        distinct(Panels.id). \
        values(Panels.name, Panels.id)
    return panel

def get_panel_by_id(s, panel_id, version=None):
    if not version:
        current_version = get_current_version(s, panel_id)
    else:
        current_version = version
    panel = s.query(Projects, Panels, Versions, Regions, Exons, Tx, Genes). \
        join(Panels). \
        join(Versions). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        join(Genes). \
        filter(and_(Panels.id == panel_id, Versions.intro <= current_version,
                    or_(Versions.last >= current_version, Versions.last == None))).order_by(Regions.start). \
        values(Projects.id.label("project_id"), Panels.name, Panels.current_version, Versions.extension_3,
               Versions.extension_5, Versions.intro,
               Versions.last, Regions.chrom, Regions.start, Regions.end, Tx.accession, Genes.name.label("genename"),
               Exons.number)

    return panel

def get_vpanel_by_gene_id(s, gene_id):
    vpanel = s.query(Genes, Tx, Exons, Regions, Versions, VPRelationships, VirtualPanels). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(and_(Genes.id == gene_id, or_(VPRelationships.last >= VirtualPanels.current_version, VPRelationships.last == None))). \
        distinct(VirtualPanels.id). \
        group_by(VirtualPanels.id). \
        values(VirtualPanels.id,VirtualPanels.name)
    return vpanel

def get_panel_by_gene_id(s, gene_id):
    panel = s.query(Genes, Tx, Exons, Regions, Versions, Panels). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(Panels). \
        filter(and_(Genes.id == gene_id, or_(Versions.last >= Panels.current_version, Versions.last == None))). \
        distinct(Panels.id). \
        group_by(Panels.id). \
        values(Panels.id, Panels.name)
    return panel

def get_vpanel_by_id(s, vpanel_id):
    current_version = get_current_vpanel_version(s, vpanel_id)



def get_vpanel_by_id(s, vpanel_id, version=None):
    if not version:
        current_version = get_current_vpanel_version(s, vpanel_id)
    else:
        current_version = version
    panel = s.query(Projects, Panels, Versions, VPRelationships, VirtualPanels, Regions, Exons, Tx, Genes). \
        join(Panels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        join(Genes). \
        filter(and_(VirtualPanels.id == vpanel_id, Versions.intro <= current_version,
                    or_(Versions.last >= current_version, Versions.last == None))).order_by(Regions.start). \
        values(Projects.id.label("project_id"), VirtualPanels.name, VirtualPanels.current_version, Versions.extension_3,
               Versions.extension_5, Versions.intro,
               Versions.last, Regions.chrom, Regions.start, Regions.end, Tx.accession, Genes.name.label("genename"),
               Exons.number)

    return panel

def get_vpanel_id_by_name(s, vpanel_name):
    vpanel = s.query(VirtualPanels). \
        filter(VirtualPanels.name == vpanel_name). \
        values(VirtualPanels.id)
    return vpanel

def get_panel_details_by_id(s, panel_id):
    panel = s.query(Projects, Panels). \
        join(Panels). \
        filter(Panels.id == panel_id). \
        values(Panels.name, Panels.current_version)

    return panel

def get_panel_id_by_name(s, panel_name):
    panel = s.query(Panels). \
        filter(Panels.name == panel_name). \
        values(Panels.id, Panels.project_id)
    return panel

def get_vpanel_details_by_id(s, vpanel_id):
    panel = s.query(Projects, Panels, Versions, VPRelationships, VirtualPanels). \
        join(Panels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(VirtualPanels.id == vpanel_id). \
        values(VirtualPanels.name, VirtualPanels.current_version, Projects.id.label('project_id'))

    return panel

def check_if_locked_by_user(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    locked = s.query(Panels).filter(or_(and_(Panels.id == panel_id, Panels.locked == user_id),
                                        and_(Panels.locked == None, Panels.id == panel_id))).count()
    if locked == 0:
        return False
    else:
        return True

def get_all_by_project_id(s,project_id):
    all = s.query(Projects,Panels,Versions,VPRelationships,VirtualPanels).\
        join(Panels).\
        join(Versions).\
        join(VPRelationships).\
        join(VirtualPanels).\
        distinct(VirtualPanels.name).\
        filter(Projects.id == project_id).\
        values(Projects.name.label('projectname'),
               Projects.id.label('projectid'),
               Panels.name.label('panelname'),
               Panels.id.label('panelid'),
               VirtualPanels.name.label('vpname'),
               VirtualPanels.id.label('vpid'))

    return all


def get_preftx_by_gene_id(s, project_id, gene_id):
    preftx = s.query(PrefTx,PrefTxVersions,Tx,Genes).\
        join(PrefTxVersions).\
        join(Tx).\
        join(Genes).\
        filter(and_(PrefTx.project_id == project_id,Genes.id == gene_id,or_(PrefTxVersions.last == PrefTx.current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro <= PrefTx.current_version)).values(PrefTxVersions.tx_id)
    for i in preftx:
        return i.tx_id

def get_upcoming_preftx_by_gene_id(s, project_id, gene_id):
    preftx = s.query(PrefTx,PrefTxVersions,Tx,Genes).\
        join(PrefTxVersions).\
        join(Tx).\
        join(Genes).\
        filter(and_(PrefTx.project_id == project_id,Genes.id == gene_id,or_(PrefTxVersions.last == PrefTx.current_version, PrefTxVersions.last == None), \
                    PrefTxVersions.intro > PrefTx.current_version)).values(PrefTxVersions.tx_id)
    for i in preftx:
        return i.tx_id

def get_tx_by_gene_id(s, gene_id):
    tx = s.query(Genes,Tx).\
        join(Tx).\
        filter(Genes.id==gene_id).values(Tx.id,Tx.accession,Genes.id.label("geneid"))
    return tx

def check_if_admin(s,username):
    """
    check if the user is an admin

    :param s: database session
    :param username: the username of the user
    :return: True or False for admin status
    """
    user_id = get_user_id_by_username(s,username)
    query = s.query(Users).filter(Users.id == user_id).values(Users.admin)
    for i in query:
        if i.admin == 1:
            return True
        else:
            return False

@message
def create_user(s,username):
    """
    create a user
    :param s: database session
    :param username: the username of the new user
    :return: True or False
    """
    user = Users(username=username,admin=0)
    try:
        s.add(user)
        s.commit()
        return True
    except:
        return False

def get_users(s):
    """
    gets all users
    :param s: database session
    :return: sql alchemy generator object
    """
    users = s.query(Users).order_by(Users.username).values(Users.id,Users.username,Users.admin)
    return users

@message
def toggle_admin_query(s,user_id):
    """
    toggles a user admin rights
    :param s: database session
    :param user_id: the id of the user
    :return: True or False
    """
    query = s.query(Users).filter(Users.id == user_id).values(Users.admin)
    for i in query:
        if i.admin == 1:
            new_value = 0
        else:
            new_value = 1
    try:
        s.query(Users).filter_by(id=user_id).update({Users.admin: new_value})
        s.commit()
        return True
    except:
        return False


def get_all_projects(s):
    """
    gets all projects, ids and names
    :param s: database session
    :return: sql alchemcy generator object
    """
    projects = s.query(Projects).values(Projects.id,Projects.name)
    return projects

def get_all_locked(s):
    """
    gets all locked panels
    :param s: database session
    :return: sql alchemy generator object
    """
    locked = s.query(Panels,Users).join(Users).filter(Panels.locked != None).values(Panels.name,Users.username,Panels.id.label("id"))
    return locked