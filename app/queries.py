from sqlalchemy import or_, desc

from app.models import *

def get_virtual_panels_simple(s):
    vpanels = s.query(VPRelationships, VirtualPanels). \
        distinct(VirtualPanels.name). \
        group_by(VirtualPanels.name). \
        join(VirtualPanels). \
        values(VirtualPanels.current_version, \
               VirtualPanels.name, \
               VirtualPanels.id,
               VPRelationships.version_id)

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
               Projects.id.label("projectid"))

    return panels


def get_virtual_panels_by_panel_id(s, id):
    vpanels = s.query(Panels, Versions, VPRelationships, VirtualPanels). \
        join(Versions). \
        filter_by(panel_id=id). \
        join(VPRelationships). \
        join(VirtualPanels). \
        values(VirtualPanels.current_version, VirtualPanels.id.label("virtualpanelid"), \
               VirtualPanels.name.label("virtualpanelname"), \
               VPRelationships.version_id, \
               Panels.id, \
               Panels.name.label("panelname"))

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
               Panels.id.label("panelid"))

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
    panel = Panels(name, int(projectid), 0)
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