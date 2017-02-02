from app.queries import *
from sqlalchemy import and_, or_
import itertools
from app.views import message
from app.mod_admin.queries import get_user_id_by_username
from app.models import *


def check_if_locked_by_user(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    locked = s.query(Panels).filter(or_(and_(Panels.id == panel_id, Panels.locked == user_id),
                                        and_(Panels.locked == None, Panels.id == panel_id))).count()
    if locked == 0:
        return False
    else:
        return True


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

def get_regions_by_panelid(s, panelid, version):
    """
    gets current regions for a given gene within a given panel

    :param s:
    :param geneid:
    :param panelid:
    :return:
    """

    sql = text("""SELECT versions.id AS version_id,
                    regions.chrom, panels.current_version, panels.name AS panel_name, genes.name AS gene_name,
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start ELSE regions.start + versions.extension_5 END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" ELSE regions."end" + versions.extension_3 END AS region_end,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM panels, versions
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = :panel_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL)
                    GROUP BY regions.id ORDER BY chrom,region_start""")
    values = {'panel_id':panelid, 'version':version}
    regions = s.execute(sql, values)
    return regions

@message
def lock_panel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: user_id})
    s.commit()
    return True