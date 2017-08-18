from app.mod_panels.queries import get_current_version, get_current_version_vp
from sqlalchemy import and_, or_

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
    vpanel_id = s.query(VirtualPanels).filter_by(name=vpanel_name).values(VirtualPanels.id)
    print(vpanel_id)
    return vpanel_id

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
