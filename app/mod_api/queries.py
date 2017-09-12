from app.mod_panels.queries import get_current_version, get_current_version_vp
from sqlalchemy import and_, or_, text

from app.mod_projects.queries import get_preftx_id_by_project_id, get_current_preftx_version, get_project_id_by_name
from app.models import *


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

def get_intronic_api(s, vpanel_name, version='current'):
    vpanel = s.query(VirtualPanels).filter_by(name=vpanel_name).values(VirtualPanels.id)
    for i in vpanel:
        vpanel_id = i.id
    print(vpanel_id)
    if version == 'current':
        current_version = get_current_version_vp(s, vpanel_id)
    else:
        current_version = version

    sql = text("""SELECT regions.chrom, regions.start - 25 as start, regions.start - 5 as end
                    FROM virtual_panels 
                    JOIN VP_relationships on virtual_panels.id = VP_relationships.vpanel_id
                    JOIN versions on VP_relationships.version_id = versions.id
                    JOIN regions ON regions.id = versions.region_id
                    WHERE virtual_panels.id = :vpanel_id AND VP_relationships.intro <= :version AND (VP_relationships.last >= :version OR VP_relationships.last IS NULL)
                    AND regions.name IS NULL
                    UNION
                    SELECT regions.chrom, regions.end + 5 as start, regions.end + 25 as end
                    FROM virtual_panels 
                    JOIN VP_relationships on virtual_panels.id = VP_relationships.vpanel_id
                    JOIN versions on VP_relationships.version_id = versions.id
                    JOIN regions ON regions.id = versions.region_id
                    WHERE virtual_panels.id = :vpanel_id AND VP_relationships.intro <= :version AND (VP_relationships.last >= :version OR VP_relationships.last IS NULL)
                    AND regions.name IS NULL
                    ORDER BY start
                        """)
    values = {"vpanel_id":vpanel_id, "version":current_version}
    regions = s.execute(sql, values)

    result = []
    # for i in regions:
    #     result.append({"chrom":i.chrom, "start":i.start, "end":i.end, "annotation":""})
    # print(result)
    return PanelApiReturn(current_version, regions)

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
