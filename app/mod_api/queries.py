from app.mod_panels.queries import get_current_version, get_current_version_vp
from sqlalchemy import and_, or_, text

from app.mod_projects.queries import get_preftx_id_by_project_id, get_current_preftx_version, get_project_id_by_name
from app.mod_panels.queries import get_panel_id_by_name
from app.models import *

class PanelApiReturn(object):
    def __init__(self, current_version, result):
        self.current_version = current_version
        self.result = result

def get_intronic_api(s, vpanel_name, version='current'):
    """
    Method to retrieve intronic regions for vpanel from database.
    The query gets the region start -25 and region start -5, region end + 5 and region end +25 for each exon.
    This does not include custom regions as these have no extension

    If the version = "current" the current version version is retrieved from the database

    :param s: SQLALchemy session token
    :param vpanel_name: name of virtual panel
    :param version: the version to get from the database
    :return: regions and current_version
    """
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

    return PanelApiReturn(current_version, regions)

def get_gene_api(s, panel, version, extension=1000):
    """
    Method to get the filled BED for a version.

    The method first creates a temporary table with all the genes included in the specified version of the panel.
    This table is then used to retrieve the minimum and maximum co-ordinates for each gene and adds a 100 bp buffer
    each side.

    :param s:
    :param panel:
    :param version:
    :param extension:
    :return:
    """
    panel_id = get_panel_id_by_name(s, panel)

    if version == "current":
        version = get_current_version(s, panel_id)

    # sql = text("DROP TABLE IF EXISTS _genes")
    # s.execute(sql)
    #
    # sql = text("""CREATE TEMP TABLE _genes AS SELECT genes.id as id
    #                 FROM genes
    #                 JOIN tx on tx.gene_id = genes.id
    #                 JOIN exons on exons.tx_id = tx.id
    #                 JOIN regions on regions.id = exons.region_id
    #                 JOIN versions on versions.region_id = regions.id
    #                 JOIN panels on panels.id = versions.panel_id
    #                 WHERE panels.id = :panel_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL);
    #             """)
    # values = {"panel_id":panel_id, "version":version}
    # s.execute(sql, values)
    #
    # sql = text("""SELECT regions.chrom as chrom, MIN(regions.start) - :extension as region_start, MAX(regions.end) + :extension as region_end, genes.name as annotation
    #                 FROM genes
    #                 JOIN tx on tx.gene_id = genes.id
    #                 JOIN exons on exons.tx_id = tx.id
    #                 JOIN regions on regions.id = exons.region_id
    #                 WHERE EXISTS (SELECT id FROM _genes WHERE id = genes.id)
    #                 GROUP BY genes.id
    #                 ORDER BY chrom, region_start
    #                     """)
    # values = {"extension":extension}
    # regions = s.execute(sql, values)

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

def get_preftx_api(s,project_name,version='current'):
    """
    Method to retrieve the preferred transcripts for a project

    If the version is "current" the query gets the current version from the database

    :param s: SQLALchemy session token
    :param project_name: name of the project to be queried
    :param version: the version to retrieve
    :return: list of key values pairs of gene and transcript and current version
    """
    project_id = get_project_id_by_name(s,project_name)
    preftx_id = get_preftx_id_by_project_id(s, project_id)
    print project_id
    if version == "current":
        current_version = get_current_preftx_version(s, preftx_id)
    else:
        current_version = version

    print current_version
    preftx = s.query(Genes, Tx, PrefTxVersions, PrefTx, Projects). \
        filter(and_(PrefTx.project_id == project_id,
                    or_(PrefTxVersions.last >= current_version, PrefTxVersions.last == None),
                    PrefTxVersions.intro <= current_version)). \
        join(Tx). \
        join(PrefTxVersions). \
        join(PrefTx). \
        join(Projects). \
        values(PrefTx.current_version,
               Tx.accession, Genes.name)

    return PanelApiReturn(current_version, preftx)
