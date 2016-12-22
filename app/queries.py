from app import models
from sqlalchemy import or_,bindparam,desc

def get_virtual_panels(s):
    """
    gets all virtual panels
    :param s: database session (initiated on app run)
    :return: sql alchemy object with study name and study id
    """
    # panels = s.query(models.Panels, models.Studies).join(models.Studies). \
    #     values(models.Panels.current_version, models.Panels.id.label("panelid"), \
    #            models.Panels.name.label("panelname"), \
    #            models.Panels.id, \
    #            models.Studies.name.label("studyname"))

    vpanels = s.query(models.VirtualPanels,models.VPRelationships,models.Versions,models.Panels). \
        join(models.Versions). \
        join(models.VPRelationships). \
        join(models.VirtualPanels). \
        values(models.VirtualPanels.current_version,\
               models.VirtualPanels.id.label("virtualpanlelid"),\
               models.VirtualPanels.name.label("virtualpanelname"),\
               models.Panels.name.label("panelname"))

    return vpanels

def get_panels(s):
    """
    gets all panels in database
    :param s: database session (initiated on app run)
    :return: sql alchemy object with study name and study id
    """
    panels = s.query(models.Projects,models.Panels).join(models.Panels). \
        values(models.Panels.name.label("panelname"),models.Panels.current_version,models.Panels.id.label("panelid"))

    return panels

def get_virtual_panels_by_panel_id(s,id):
    vpanels = s.query(models.Panels,models.Versions,models.VPRelationships,models.VirtualPanels). \
        join(models.Versions). \
        join(models.VPRelationships). \
        join(models.VirtualPanels). \
        filter_by(panel_id=id). \
        values(models.Panels.current_version, models.VirtualPanels.id.label("virtualpanelid"), \
               models.Panels.name.label("virtualpanelname"), \
               models.Panels.id, \
               models.Panels.name.label("panelname"))

    return vpanels

def get_panels_by_project_id(s,id):
    panels = s.query(models.Projects,models.Panels).join(models.Panels).filter_by(project_id=id). \
        values(models.Panels.name.label("panelname"),models.Panels.current_version,models.Panels.id.label("panelid"))

    return panels

# def check_panel_status(s,id):
#     panels = s.query(models.Panels,models.Versions).filter_by(id=1).join(models.Versions).\
#         values(models.Panels.current_version,\
#                models.Versions.last,\
#                models.Versions.intro)
#     status = True
#     for i in panels:
#         if i.last is not None:
#             if i.intro > i.current_version:
#                 status = False
#                 break
#             if i.last == i.current_version:
#                 status = False
#                 break
#
#     return status

def check_panel_status(s,id):
    studies = s.query(models.Panels,models.Versions).filter_by(id=id).join(models.Versions).\
        values(models.Panels.name,\
                models.Panels.current_version,\
               models.Versions.last,\
               models.Versions.intro)
    status = True
    for i in studies:
        if i.intro > i.current_version:
            status = False
            break
        if i.last is not None:
            if i.last == i.current_version:
                status = False
                break

    return status

def get_panel_current(s,id,version):

    query = s.query(models.Panels, models.Versions, models.Genes, models.Tx, models.Exons, models.Regions). \
        filter(models.Panels.id == id, models.Versions.intro <= version, \
               or_(models.Versions.last >= version, \
                   models.Versions.last == None)).\
            join(models.Versions). \
            join(models.Regions). \
            join(models.Exons). \
            join(models.Tx). \
            join(models.Genes).values(models.Panels.id.label("panelid"), \
                                      models.Panels.current_version, \
                                      models.Panels.name.label("panelname"), \
                                      models.Versions.intro, \
                                      models.Versions.last, \
                                      models.Versions.region_id, \
                                      models.Versions.id, \
                                      models.Versions.extension_3, \
                                      models.Versions.extension_5, \
                                      models.Genes.name.label("genename"), \
                                      models.Regions.chrom, \
                                      models.Regions.start, \
                                      models.Regions.end, \
                                      models.Exons.number, \
                                      models.Tx.accession)

    return query


def get_panel_edit(s,id,version):

    query = s.query(models.Panels, models.Versions, models.Genes, models.Tx, models.Exons, models.Regions). \
        filter(models.Panels.id == id, \
               or_(models.Versions.last > version, \
                   models.Versions.last == None)).\
        order_by(desc(models.Regions.start)). \
        join(models.Versions). \
        join(models.Regions). \
        join(models.Exons). \
        join(models.Tx). \
        join(models.Genes).values(models.Panels.id.label("panelid"), \
                                  models.Panels.current_version, \
                                  models.Panels.name.label("panelname"), \
                                  models.Versions.intro, \
                                  models.Versions.last, \
                                  models.Versions.region_id, \
                                  models.Versions.id, \
                                  models.Versions.extension_3, \
                                  models.Versions.extension_5, \
                                  models.Genes.name.label("genename"), \
                                  models.Regions.chrom, \
                                  models.Regions.start, \
                                  models.Regions.end, \
                                  models.Exons.number, \
                                  models.Tx.accession)

    return query


def get_current_version(s,panelid):
    version = s.query(models.Panels).filter_by(id=panelid).values(models.Panels.current_version)
    for i in version:
        return i.current_version

def create_panel_query(s,projectid,name):
    panel = models.Panels(name,int(projectid),0)
    s.add(panel)
    s.commit()
    return panel.id

def add_region_to_panel(s,regionid,panelid):
    print panelid
    current = get_current_version(s,panelid)
    print current
    version = models.Versions(int(current)+1,None,panelid,regionid,None,None,None)
    s.add(version)
    return version.id

def add_genes_to_panel(s,panelid,gene):
    #gets all regions for gene
    query = s.query(models.Genes,models.Tx,models.Exons,models.Regions). \
        filter(models.Genes.name == gene). \
        join(models.Tx). \
        join(models.Exons). \
        join(models.Regions).values(models.Regions.id)
    #adds them to the panel
    for i in query:
        add_region_to_panel(s,i.id,panelid)
    s.commit()
