from sqlalchemy import and_, or_, desc, text, exc

from models import *
from panel_pal import message


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

#TODO mod_projects?
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

def get_project_id_by_panel_id(s, panelid):
    project = s.query(Projects, Panels).join(Panels).filter(Panels.id == panelid).values(Projects.id)
    for i in project:
        return i.id

#TODO ?not used anywhere
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
        order_by(Genes.name).\
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

#TODO ?search queries
def get_gene_from_tx(s,tx_id):
    genes = s.query(Tx, Genes). \
        join(Genes). \
        filter(Tx.id == tx_id). \
        values(Genes.name, Genes.id)
    return genes

def get_tx_id_from_name(s,tx_name):
    trans = s.query(Tx).filter(Tx.accession == tx_name).values(Tx.id)
    for i in trans:
        return i.id

def get_panel_by_vpanel_id(s, vp_id):
    panel = s.query(Panels, Versions, VPRelationships, VirtualPanels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(VirtualPanels.id == vp_id). \
        distinct(Panels.id). \
        values(Panels.name, Panels.id)
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

def get_vpanel_id_by_name(s, vpanel_name):
    vpanel = s.query(VirtualPanels). \
        filter(VirtualPanels.name == vpanel_name). \
        values(VirtualPanels.id)
    return vpanel

def get_panel_id_by_name(s, panel_name):
    panel = s.query(Panels). \
        filter(Panels.name == panel_name). \
        values(Panels.id, Panels.project_id)
    return panel






def get_gene_id_from_name(s,gene_name):
    gene = s.query(Genes).filter(Genes.name == gene_name).values(Genes.id)
    for i in gene:
        return i.id

def get_user_by_username(s, username):
    user = s.query(Users).filter_by(username=username)
    return user

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



#TODO ?mod_projects queries
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




def get_tx_by_gene_id(s, gene_id):
    tx = s.query(Genes,Tx).\
        join(Tx).\
        filter(Genes.id==gene_id).order_by(Genes.name).values(Tx.id,Tx.accession,Genes.id.label("geneid"))
    return tx


#TODO ?mod_admin queries
def get_users(s):
    """
    gets all users
    :param s: database session
    :return: sql alchemy generator object
    """
    users = s.query(Users).order_by(Users.username).values(Users.id,Users.username,Users.admin)
    return users



def get_all_locked(s):
    """
    gets all locked panels
    :param s: database session
    :return: sql alchemy generator object
    """
    locked = s.query(Panels,Users).join(Users).filter(Panels.locked != None).values(Panels.name,Users.username,Panels.id.label("id"))
    return locked



def get_all_locked_by_username(s,username):
    """
    gets all locked panels
    :param s: database session
    :return: sql alchemy generator object
    """
    # print username
    # user_id = get_user_by_username(s,username)
    # print user_id
    locked = s.query(Panels,Users).\
        join(Users).\
        filter(Users.username == username).\
        values(Panels.name,Users.username,Panels.id.label("id"))
    return locked