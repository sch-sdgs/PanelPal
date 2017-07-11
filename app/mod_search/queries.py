from sqlalchemy import and_, or_
from app.models import *

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