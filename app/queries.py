from sqlalchemy import and_, or_, desc, text, exc

from models import *
from main import message

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



def get_project_id_by_panel_id(s, panelid):
    project = s.query(Projects, Panels).join(Panels).filter(Panels.id == panelid).values(Projects.id)
    for i in project:
        return i.id

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



def get_gene_id_from_name(s,gene_name):
    gene = s.query(Genes).filter(Genes.name == gene_name).values(Genes.id)
    for i in gene:
        return i.id

def get_tx_id_from_name(s,tx_name):
    trans = s.query(Tx).filter(Tx.accession == tx_name).values(Tx.id)
    for i in trans:
        return i.id


def get_user_by_username(s, username):
    user = s.query(Users).filter_by(username=username)
    return user



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
        filter(Genes.id==gene_id).values(Tx.id,Tx.accession,Genes.id.label("geneid"))
    return tx



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