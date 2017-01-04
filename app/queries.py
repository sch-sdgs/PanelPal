from sqlalchemy import and_, or_, desc

from app.models import *


def get_virtual_panels_simple(s):
    vpanels = s.query(VirtualPanels, VPRelationships, Versions, Panels). \
        group_by(VirtualPanels.name). \
        join(VPRelationships). \
        join(Versions). \
        join(Panels). \
        values(VirtualPanels.current_version, \
               VirtualPanels.name.label('vp_name'), \
               VirtualPanels.id,
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


def get_virtual_panels_by_panel_id(s, id):
    vpanels = s.query(VirtualPanels, VPRelationships, Versions, Panels). \
        distinct(VirtualPanels.name). \
        group_by(VirtualPanels.name). \
        join(VPRelationships). \
        join(Versions). \
        join(Panels). \
        filter(Panels.id == id). \
        values(VirtualPanels.id, \
               VirtualPanels.current_version, \
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
    return version.id


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


def make_panel_live(s, panelid, new_version):
    """
    makes a panel line

    :return: True
    :param s: db session
    :param panelid: panel id
    :param new_version: the new version number of the panel
    """
    s.query(Panels).filter_by(id=panelid).update({Panels.current_version: new_version})
    s.commit()

    return True


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
                    PrefTxVersions.intro >= PrefTx.current_version)). \
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
               Tx.accession, \
               Tx.tx_start, \
               Tx.tx_end, \
               Tx.strand)
    return genes


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


def add_preftxs_to_panel(s, project_id, tx_ids):
    query = get_preftx_current_version(s, project_id)
    current_version = query[0]
    preftx_id = query[1]
    print preftx_id
    print "current_version:" + str(current_version)
    for tx_id in tx_ids:
        print tx_id
        preftx = PrefTxVersions(s, pref_tx_id=preftx_id, tx_id=tx_id, intro=current_version + 1, last=None)
        s.add(preftx)
        s.flush()
        print preftx.id
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


def add_user_project_rel(s, user_id, project_id):
    rel = UserRelationships(user_id=user_id, project_id=project_id)
    s.add(rel)
    s.commit()
    return True


def get_projects_by_user(s, username):
    user_id = get_user_id_by_username(s, username)
    projects = s.query(Projects, UserRelationships).join(UserRelationships).filter_by(user_id=user_id).values(
        Projects.id.label('id'), Projects.name.label('name'))
    print type(projects)
    return projects


def check_user_has_permission(s, username, project_id):
    if username == "dnamdp":
        return True
    check = s.query(Users, UserRelationships).join(UserRelationships).filter(
        and_(Users.username == username, UserRelationships.project_id == project_id)).count()
    print check
    if check == 0:
        return False
    else:
        return True


def lock_panel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: user_id})
    s.commit()
    return True


def unlock_panel(s, panel_id):
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: None})
    s.commit()
    return True


def get_username_by_user_id(s, user_id):
    username = s.query(Users).filter_by(id=user_id).values(Users.username)
    for i in username:
        return i.username

class PanelApiReturn(object):
  def __init__(self, current_version, panel):
     self.current_version = current_version
     self.panel = panel

def get_panel_api(s, panel_name, version='current'):
    panel_ids = s.query(Panels).filter_by(name=panel_name).values(Panels.id)
    for i in panel_ids:
        panel_id = i.id
    if version == "current":
        current_version = get_current_version(s, panel_id)
    else:
        current_version = version
    panel = s.query(Panels,Versions,Regions,Exons,Tx,Genes).\
        join(Versions).\
        join(Regions).\
        join(Exons).\
        join(Tx).\
        join(Genes).\
        filter(and_(Panels.id == panel_id,Versions.intro <= current_version,or_(Versions.last >= current_version, Versions.last == None))).order_by(Regions.start)
    return PanelApiReturn(current_version,panel)

def get_vpanel_api(s, panel_name, version='current'):
    panel_ids = s.query(VirtualPanels).filter_by(name=panel_name).values(VirtualPanels.id)
    for i in panel_ids:
        panel_id = i.id
    if version == "current":
        current_version = get_current_version_vp(s, panel_id)
    else:
        current_version = version
    panel = s.query(VirtualPanels,VPRelationships,Versions,Regions,Exons,Tx,Genes).\
        join(VPRelationships).\
        join(Versions).\
        join(Regions).\
        join(Exons).\
        join(Tx).\
        join(Genes).\
        filter(and_(VirtualPanels.id == panel_id,VPRelationships.intro <= current_version,or_(VPRelationships.last >= current_version, VPRelationships.last == None))).order_by(Regions.start)
    return PanelApiReturn(current_version,panel)

def get_exonic_api(s, panel_name, version='current'):
    panel_ids = s.query(VirtualPanels).filter_by(name=panel_name).values(VirtualPanels.id)
    for i in panel_ids:
        panel_id = i.id
    if version == "current":
        current_version = get_current_version_vp(s, panel_id)
    else:
        current_version = version
    panel = s.query(VirtualPanels,VPRelationships,Versions,Regions,Exons,Tx,Genes).\
        join(VPRelationships).\
        join(Versions).\
        join(Regions).\
        join(Exons).\
        join(Tx).\
        join(Genes).\
        filter(and_(VirtualPanels.id == panel_id,VPRelationships.intro <= current_version,or_(VPRelationships.last >= current_version, VPRelationships.last == None))).order_by(Regions.start)
    return PanelApiReturn(current_version,panel)

