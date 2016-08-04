from app import models
from sqlalchemy import or_,bindparam,desc



def get_panels(s):
    panels = s.query(models.Panels, models.Projects).join(models.Projects). \
        values(models.Panels.current_version, models.Panels.id.label("panelid"), \
               models.Panels.name.label("panelname"), \
               models.Panels.id, \
               models.Projects.name.label("projectname"))

    return panels

def get_panels_by_project_id(s,id):
    panels = s.query(models.Panels, models.Projects).join(models.Projects).filter_by(id=id). \
        values(models.Panels.current_version, models.Panels.id.label("panelid"), \
               models.Panels.name.label("panelname"), \
               models.Panels.id, \
               models.Projects.name.label("projectname"))

    return panels

def check_panel_status(s,id):
    panels = s.query(models.Panels,models.Versions).filter_by(id=1).join(models.Versions).\
        values(models.Panels.current_version,\
               models.Versions.last,\
               models.Versions.intro)
    status = True
    for i in panels:
        if i.last is not None:
            if i.intro > i.current_version:
                status = False
                break
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
