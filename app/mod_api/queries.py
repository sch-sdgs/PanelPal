from app.mod_panels.queries import get_current_version, get_current_version_vp
from sqlalchemy import and_, or_, text

from app.mod_projects.queries import get_preftx_id_by_project_id, get_current_preftx_version
from app.models import *

class PanelApiReturn(object):
    def __init__(self, current_version, result):
        self.current_version = current_version
        self.result = result

def get_intronic_api(s, vpanel_id, version='current'):
    """
    Method to retrieve intronic regions for vpanel from database.
    The query gets the region start -25 and region start -5, region end + 5 and region end +25 for each exon.
    This does not include custom regions as these have no extension

    If the version = "current" the current version version is retrieved from the database

    :param s: SQLALchemy session token
    :param vpanel_id: name of virtual panel
    :param version: the version to get from the database
    :return: regions and current_version
    """
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

    return PanelApiReturn(current_version, regions)

def get_gene_api(s, panel_id, version, extension=1000):
    """
    Method to get the filled BED for a version.

    The method first creates a temporary table with all the genes included in the specified version of the panel.
    This table is then used to retrieve the minimum and maximum co-ordinates for each gene and adds a 100 bp buffer
    each side.

    :param s:
    :param panel_id:
    :param version:
    :param extension:
    :return:
    """

    sql = """SELECT genes.id as gene_id, regions.chrom as chrom, MIN(regions.start) - :extension as region_start, MAX(regions.end) + :extension as region_end, genes.name as annotation
                    FROM genes
                    JOIN tx on tx.gene_id = genes.id
                    JOIN exons on exons.tx_id = tx.id
                    JOIN regions on regions.id = exons.region_id
                    JOIN versions on versions.region_id = regions.id
                    JOIN panels on panels.id = versions.panel_id
                    WHERE panels.id = :panel_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL) GROUP BY genes.id;"""
    values = {"panel_id": panel_id, "version": version, "extension":extension}
    regions = s.execute(sql, values)

    return PanelApiReturn(version, regions)

def get_preftx_api(s,project_id,version='current'):
    """
    Method to retrieve the preferred transcripts for a project

    If the version is "current" the query gets the current version from the database

    :param s: SQLALchemy session token
    :param project_id: name of the project to be queried
    :param version: the version to retrieve
    :return: list of key values pairs of gene and transcript and current version
    """
    preftx_id = get_preftx_id_by_project_id(s, project_id)
    if version == "current":
        current_version = get_current_preftx_version(s, preftx_id)
    else:
        current_version = version

    print current_version
    preftx = s.query(Genes, Tx, PrefTxVersions, PrefTx, Projects). \
        filter(and_(PrefTx.project_id == project_id,
                    or_(PrefTxVersions.last.is_(None), PrefTxVersions.last >= current_version),
                    PrefTxVersions.intro <= current_version)). \
        join(Tx). \
        join(PrefTxVersions). \
        join(PrefTx). \
        join(Projects). \
        values(PrefTx.current_version,
               Tx.accession, Genes.name)

    return PanelApiReturn(current_version, preftx)

def get_project_from_vp(s, vp_id):
    """
    Gets the project ID for a given virtual panel ID

    :param s:
    :param vp_id:
    :return:
    """
    project = s.query(Projects, Panels, Versions, VPRelationships).\
        filter(VPRelationships.vpanel_id == vp_id).\
        join(Panels).join(Versions).join(VPRelationships).group_by(Panels.project_id).values(Projects.id, Projects.name)
    for p in project:
        return p

def get_vpanel_id_from_testcode(s, test_code):
    """
    Method to get the virtual panel ID from the TestCode assigned in StarLIMS

    :param s:
    :param test_code:
    :return:
    """
    vpanel = s.query(TestCodes).filter(TestCodes.test_code == test_code).first()
    return vpanel.vpanel_id, vpanel.version