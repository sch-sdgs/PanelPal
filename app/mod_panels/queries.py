from decimal import *

from sqlalchemy import and_, or_, case, text, exc, desc

from app.mod_admin.queries import get_user_id_by_username, check_user_has_permission
from app.panel_pal import message
from app.models import *


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

def get_project_id_by_panel_id(s, panelid):
    project = s.query(Projects, Panels).join(Panels).filter(Panels.id == panelid).values(Projects.id)
    for i in project:
        return i.id

def get_genes_by_panelid(s, panelid, current_version):
    genes = s.query(Genes, Tx, Exons, Regions, Versions, Panels). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(Panels). \
        filter(and_(Panels.id == panelid, Versions.intro <= current_version,
                    or_(Versions.last >= current_version, Versions.last == None))). \
        values(Genes.name,
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
        filter(and_(VirtualPanels.id == vpanel_id, VPRelationships.intro <= current_version,
                    or_(VPRelationships.last >= current_version, VPRelationships.last == None))). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        values(Genes.name, Genes.id)

    return genes


@message
def unlock_panel_query(s, panel_id):
    s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: None})
    s.commit()
    return True

def get_locked_user(s, panel_id):
    """
    returns the username of the person who locked the panel

    :param s:
    :param panel_id:
    :return:
    """
    users = s.query(Panels,Users).join(Users).filter(Panels.id == panel_id).values(Users.username)
    for i in users:
        return i.username


def get_all_locked_by_username(s,username):
    """
    gets all locked panels
    :param s: database session
    :return: sql alchemy generator object
    """
    locked = s.query(Panels,Users).\
        join(Users).\
        filter(Users.username == username).\
        values(Panels.name,Users.username,Panels.id.label("id"))
    return locked

def check_if_locked(s, panel_id):
    locked = s.query(Panels).filter(Panels.id == panel_id).values(Panels.locked)
    # locked = s.query(Panels).filter(and_(Panels.locked == None, Panels.id == panel_id)).count()
    for i in locked:
        return i.locked


def check_if_locked_by_user_vpanel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    locked = s.query(Panels).filter(or_(and_(Panels.id == panel_id, Panels.locked == user_id),
                                        and_(Panels.locked == None, Panels.id == panel_id))).values(Panels.locked)
    # locked = s.query(Panels).filter(and_(Panels.locked == None, Panels.id == panel_id)).values(Panels.locked)
    for i in locked:
        return i.locked


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


@message
def create_panel_query(s, projectid, name, username):
    """
    creates an entry in the panels table ready for regions(versions) to be added

    :param s: db session
    :param projectid: project id
    :param name: panel name
    :param username:
    :return: panel id
    """
    try:
        user_id = get_user_id_by_username(s, username)
        panel = Panels(name=name, project_id=int(projectid), current_version=0, locked=user_id)
        s.add(panel)
        s.commit()
        return panel.id
    except exc.IntegrityError:
        return -1


@message
def create_virtualpanel_query(s, name, panel_id):
    """
    creates a virtual panel in the virtual panels table and adds the vp_relationship to the broad panel

    :param s: db session
    :param name: name of virtual panel
    :param panel_id: id of the parent panel
    :return: virtual panel id
    """
    try:
        current_panel_version = get_current_version(s, panel_id)
        virtualpanel = VirtualPanels(name, float(current_panel_version))
        s.add(virtualpanel)
        s.commit()
        return virtualpanel.id
    except exc.IntegrityError:
        s.rollback()
        return -1


def get_panel_info(s, panel_id):
    """

    :param s:
    :param panel_id:
    :return:
    """
    panel_info = s.query(Panels, Projects).join(Projects).filter(Panels.id == panel_id).values(
        Panels.current_version,
        Panels.name,
        Panels.locked,
        Projects.id.label('project_id'),
        Projects.name.label('project_name')
    )
    for i in panel_info:
        return i


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
def remove_panel_query(s, panel_name):
    """
    removes panel from panels table - only to be used when no versions have been added to the panel

    :param s:
    :param panel_name:
    :return:
    """
    s.query(Panels).filter_by(name=panel_name).delete()
    s.commit()
    return True


@message
def add_region_to_panel(s, regionid, panelid, ext_3=None, ext_5=None):
    """
    called by other query method - this method DOES NOT COMMIT CHANGES TO THE DATABASE
    THIS METHOD MUST BE USED WITH OTHER METHODS

    :param s: db session
    :param regionid: region id
    :param panelid: panel id
    :return: the id in the versions table
    """
    current = get_current_version(s, panelid)
    if not current:
        current = 0
    version = Versions(intro=int(current) + 1, last=None, panel_id=panelid, region_id=regionid, comment=None,
                       extension_3=ext_3, extension_5=ext_5)
    s.add(version)
    # s.commit()
    return version

@message
def add_genes_to_panel_with_ext(s, panel_id, gene_id):
    """
    Gets all region for gene with extensions to remove UTR and adds to versions table

    :param s:
    :param panel_id:
    :param gene_id:
    :return:
    """
    regions = get_regions_by_gene_no_utr(s, gene_id)
    for r in regions:
        add_region_to_panel(s, r.region_id, panel_id, ext_3=r.ext_3, ext_5=r.ext_5)
    s.commit()

    return True

def add_all_regions_to_vp(s, panel_id, gene_id, vpanel_id):
    """
    Add all the current panel regions to the virtual panel for a given gene

    :param s:
    :param panel_id:
    :param gene_id:
    :param vpanel_id:
    :return:
    """
    regions = get_panel_regions_by_geneid(s, gene_id, panel_id)
    for r in regions:
        add_version_to_vp(s, vpanel_id, r.version_id)
    s.commit()
    return True

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
    Adds a row from versions to the VP_relationships table.
    This method does not commit - must be committed following use.

    :param s:
    :param vp_id:
    :param version_id:
    :return:
    """
    current_version = get_current_version_vp(s, vp_id)
    if not current_version:
        panel_id = get_panel_by_vp_id(s, vp_id)
        current_version = get_current_version(s,panel_id)
    vp_relationship = VPRelationships(intro=float(current_version) + float(0.1), last=None, version_id=version_id, vpanel_id=vp_id)
    s.add(vp_relationship)
    # s.commit()
    return vp_relationship.id

def get_prev_versions_vp(s, vp_id):
    """

    :param s:
    :param vp_id:
    :return:
    """
    sql = text("DROP TABLE IF EXISTS _intro;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _intro AS
                    SELECT DISTINCT VP_relationships.intro
                    FROM VP_relationships
                    WHERE VP_relationships.vpanel_id = :vp_id;""")

    values = {"vp_id": vp_id}
    s.execute(sql, values)
    sql = text("""SELECT DISTINCT VP_relationships.last as val
                    FROM VP_relationships
                    WHERE VP_relationships.vpanel_id = :vp_id
                    AND val IS NOT NULL
                    AND NOT EXISTS (SELECT * FROM _intro WHERE intro LIKE val)
                    UNION SELECT intro as val FROM _intro
                    ORDER BY val;""")
    versions = s.execute(sql, values)

    results = []
    for v in versions:
        results.append(v.val)
    return results

@message
def create_custom_region(s, panel_id, chrom, start, end, name):
    """
    Adds custom region to regions table and inserts for relevant panel in versions table

    :param s:
    :param panel_id:
    :param chrom:
    :param start:
    :param end:
    :param name:
    :return:
    """
    region = Regions(chrom=chrom, start=start, end=end, name=name)
    s.add(region)
    s.commit()
    version_id = add_region_to_panel(s, region.id, panel_id)
    s.commit()
    return region.id, version_id


def select_region_by_location(s, chrom, start, end):
    """
    checks that custom region does not already exist

    :param s:
    :param chrom:
    :param start:
    :param end:
    :return:
    """
    regions = s.query(Regions).filter_by(chrom=chrom, start=start, end=end).all()
    return regions


def get_custom_regions_query(s, panelid):
    """

    :param s:
    :param panelid:
    :return:
    """
    chrom_order = case(((Regions.chrom == 'chr1', 1), (Regions.chrom == 'chr2', 2), (Regions.chrom == 'chr3', 3),
                        (Regions.chrom == 'chr4', 4), (Regions.chrom == 'chr5', 5), (Regions.chrom == 'chr6', 6),
                        (Regions.chrom == 'chr7', 7), (Regions.chrom == 'chr8', 8), (Regions.chrom == 'chr9', 9),
                        (Regions.chrom == 'chr10', 10), (Regions.chrom == 'chr11', 11), (Regions.chrom == 'chr12', 12),
                        (Regions.chrom == 'chr13', 13), (Regions.chrom == 'chr14', 14), (Regions.chrom == 'chr15', 15),
                        (Regions.chrom == 'chr16', 16), (Regions.chrom == 'chr17', 17), (Regions.chrom == 'chr18', 18),
                        (Regions.chrom == 'chr19', 19), (Regions.chrom == 'chr20', 20), (Regions.chrom == 'chr21', 21),
                        (Regions.chrom == 'chr22', 22), (Regions.chrom == 'chrX', 23), (Regions.chrom == 'chrY', 24)))
    current_version = get_current_version(s, panelid)

    custom_regions = s.query(Versions, Regions).join(Regions). \
        filter(and_(Versions.panel_id == panelid,
                    or_(
                        and_(Versions.intro == current_version,
                             or_(Versions.last == None, Versions.last >= current_version)),
                        Versions.intro == current_version + 1),
                    or_(Versions.last >= current_version, Versions.last == None),
                    Regions.name.isnot(None))). \
        order_by(chrom_order, Regions.start). \
        values(Versions.id.label("version_id"), Regions.id.label("region_id"), Regions.chrom,
               case([(Versions.extension_5 == None, Regions.start)], else_=Regions.start + Versions.extension_5).label(
                   'region_start'),
               case([(Versions.extension_3 == None, Regions.end)], else_=Regions.end + Versions.extension_3).label(
                   'region_end'),
               Regions.name)
    return custom_regions


def get_current_custom_regions(s, vpanel_id):
    """
    Gets custom regions currently included in panel

    :param s:
    :param vpanel_id:
    :return:
    """
    ids = s.query(VPRelationships, Versions, Regions). \
        join(Versions). \
        join(Regions). \
        group_by(Versions.id). \
        filter(and_(VPRelationships.vpanel_id == vpanel_id, Regions.name.isnot(None))). \
        values(Versions.id)
    return ids


def get_vprelationships(s, vp_id, gene_id):
    """
    Gets all current VPRelationship ids for virtual panel

    :param s:
    :param vp_id:
    :param gene_id:
    :return:
    """
    current_version = get_current_version_vp(s, vp_id)
    versions = s.query(VPRelationships, Versions, Regions, Exons, Tx). \
        join(Versions). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        filter(and_(Tx.gene_id == gene_id,
                    VPRelationships.vpanel_id == vp_id,
                    VPRelationships.intro <= float(current_version) + 0.1,
                    or_(VPRelationships.last > current_version, VPRelationships.last == None)
                    )
               ). \
        group_by(VPRelationships.version_id). \
        values(VPRelationships.version_id)
    return versions


def get_versions(s, panel_id, gene_id):
    """
    Gets the version ids for all the regions in a certain gene that have been included in the panel

    :param s:
    :param panel_id:
    :param gene_id:
    :return:
    """
    current_version = get_current_version(s, panel_id)
    if not current_version:
        current_version = 0
    versions = s.query(Versions, Regions, Exons, Tx). \
        join(Regions). \
        join(Exons). \
        join(Tx). \
        filter(and_(Tx.gene_id == gene_id, Versions.panel_id == panel_id,
                    or_(Versions.intro == current_version + 1,
                        and_(Versions.intro <= current_version,
                             or_(Versions.last > current_version, Versions.last == None)
                             )
                        )
                    )
               ). \
        group_by(Versions.id). \
        values(Regions.id)
    return versions


def get_panel_by_vp_id(s, vp_id):
    panel = s.query(VirtualPanels, VPRelationships, Versions).join(VPRelationships).join(Versions).distinct(
        Versions.panel_id).group_by(Versions.panel_id).filter(VirtualPanels.id == vp_id).values(Versions.panel_id)
    for i in panel:
        return i.panel_id

def get_panel_by_vp_name(s, vp_name):
    panel = s.query(VirtualPanels, VPRelationships, Versions).join(VPRelationships).join(Versions).distinct(
        Versions.panel_id).group_by(Versions.panel_id).filter(VirtualPanels.name == vp_name).values(Versions.panel_id)
    for i in panel:
        return i.panel_id

def check_if_utr(s, geneid, panelid):
    """
    Checks the coordinates to see if the versions include utr

    :param s:
    :param geneid:
    :param panelid:
    :return:
    """
    current_regions = list(get_regions_by_geneid_with_versions(s, geneid, panelid))
    excl_utr = list(get_regions_by_gene_no_utr(s, geneid))
    if len(excl_utr) == 0:
        return True
    if current_regions[0].region_id == excl_utr[0].region_id and current_regions[0].region_start - current_regions[
        0].ext_5 == excl_utr[0].region_start - excl_utr[0].ext_5 and \
                    current_regions[-1].region_id == excl_utr[-1].region_id and current_regions[-1].region_end + \
            current_regions[-1].ext_3 == excl_utr[-1].region_end + excl_utr[-1].ext_3:
        return False
    elif current_regions[0].region_id != excl_utr[0].region_id and \
                            current_regions[-1].region_end + current_regions[-1].ext_3 == excl_utr[-1].region_end + \
                    excl_utr[-1].ext_3:
        return False
    elif current_regions[-1].region_id != excl_utr[-1].region_id and \
                            current_regions[0].region_start - current_regions[0].ext_5 == excl_utr[0].region_start - \
                    excl_utr[0].ext_5:
        return False
    else:
        return True

def get_altered_region_ids_exclude(s, geneid, panelid):
    """

    :param s:
    :param geneid:
    :param panelid:
    :return:
    """
    sql = text("DROP TABLE IF EXISTS _cds_alt;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _cds_alt AS
        SELECT regions.id as id, min(tx.cds_start) AS cds_start, max(tx.cds_end) AS cds_end
        FROM tx
        JOIN exons on tx.id = exons.tx_id
        JOIN regions ON exons.region_id = regions.id
        WHERE tx.gene_id = :gene_id
        GROUP BY regions.id;""")
    values = {'gene_id':geneid}
    s.execute(sql, values)


    sql = text("""SELECT DISTINCT regions.id as region_id,
                    regions.start AS region_start,
                    CASE WHEN (regions.start < (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id))
                            THEN regions.start - (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id)
                        ELSE 0 END AS ext_5,
                    regions."end" AS region_end,
                    CASE WHEN (regions.end > (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id))
                            THEN (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id) - regions.end
                        ELSE 0 END AS ext_3,
                    CASE WHEN (versions.extension_5 != (regions.start - (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id)))
                            THEN 'True'
                        WHEN (versions.extension_5 IS NULL AND regions.start < (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id))
                            THEN 'True'
                        WHEN regions.start > (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id)
                            THEN 'True'
                        ELSE 'False' END AS include_start,
                    CASE WHEN (versions.extension_3 != ((SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id) - regions.end))
                            THEN 'True'
                        WHEN (versions.extension_3 IS NULL AND regions.end > (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id))
                            THEN 'True'
                        WHEN regions.end < (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id)
                            THEN 'True'
                        ELSE 'False' END AS include_end
                    FROM versions
                    JOIN regions ON versions.region_id = regions.id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    AND versions.panel_id = :panel_id
                    AND (versions.intro = :new_version OR (versions.intro <= :current_version AND (versions.last > :current_version OR versions.last IS NULL)))
                    AND (include_start == 'True' OR include_end == 'True')""")
    current_version = get_current_version(s, panelid)
    values = {'gene_id':geneid, 'panel_id':panelid, 'current_version':current_version, 'new_version':current_version + 1}
    regions = s.execute(sql, values)

    results = {}
    for r in regions:
        if r.include_start == 'True' and r.include_end == 'True':
            results[r.region_id] = {'coord': (r.region_start, r.region_end), 'position': 'both'}
        elif r.include_start == 'True':
            results[r.region_id] = {'coord':r.region_start - r.ext_5, 'position':'start'}
        elif r.include_end == 'True':
            results[r.region_id] = {'coord':r.region_end + r.ext_3, 'position':'end'}

    s.commit()
    s.flush()
    print(results)
    return results

def get_altered_region_ids_include(s, geneid, panelid):
    """

    :param s:
    :param geneid:
    :param panelid:
    :return:
    """
    sql = text("DROP TABLE IF EXISTS _cds_alt;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _cds_alt AS
                    SELECT regions.id as id, min(tx.cds_start) AS cds_start, max(tx.cds_end) AS cds_end
                    FROM tx
                    JOIN exons on tx.id = exons.tx_id
                    JOIN regions ON exons.region_id = regions.id
                    WHERE tx.gene_id = :gene_id
                    GROUP BY regions.id;""")
    values = {'gene_id':geneid}
    s.execute(sql, values)

    sql = text("DROP TABLE IF EXISTS _utr;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _utr AS
                    SELECT regions.id as region_id,
                    regions.start AS region_start,
                    regions."end" AS region_end,
                    'True' AS include_start,
                    'True' AS include_end
                    FROM regions
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    AND (regions.start > (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id)
                    OR regions.end < (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id))
                    GROUP BY regions.id;""")
    s.execute(sql, values)

    sql = text("""SELECT DISTINCT regions.id AS region_id,
        regions.start, regions.end,
        CASE WHEN (versions.extension_5 == (regions.start - (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id)))
		        THEN 'True'
            WHEN (versions.extension_5 IS NULL AND regions.start < (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id))
                THEN 'True'
            WHEN regions.start > (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id)
                THEN 'True'
            ELSE 'False' END AS include_start,
        CASE WHEN (versions.extension_3 == ((SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id) - regions.end))
                THEN 'True'
            WHEN (versions.extension_3 IS NULL AND regions.end > (SELECT cds_end FROM _cds_alt WHERE _cds_alt.id = regions.id))
                THEN 'True'
            WHEN regions.end < (SELECT cds_start FROM _cds_alt WHERE _cds_alt.id = regions.id)
                THEN 'True'
            ELSE 'False' END AS include_end
        FROM versions
        JOIN regions ON versions.region_id = regions.id
        JOIN exons ON regions.id = exons.region_id
        JOIN tx ON tx.id = exons.tx_id
        JOIN genes ON genes.id = tx.gene_id
        WHERE genes.id = :gene_id
        AND versions.panel_id = :panel_id
        AND (versions.intro = :new_version OR (versions.intro <= :current_version AND (versions.last > :current_version OR versions.last IS NULL)))
        AND (include_start == 'True' OR include_end == 'True')
        UNION
        SELECT region_id, region_start, region_end, include_start, include_end FROM _utr ORDER BY region_start;""")
    current_version = get_current_version(s, panelid)
    values = {'gene_id': geneid, 'panel_id': panelid, 'current_version': current_version,
              'new_version': current_version + 1}
    regions = s.execute(sql, values)

    results = {}
    for r in regions:
        if r.include_start == 'True' and r.include_end == 'True':
            results[r.region_id] = {'coord': (r.start, r.end), 'position': 'both'}
        elif r.include_start == 'True':
            results[r.region_id] = {'coord':r.start, 'position':'start'}
        else:
            results[r.region_id] = {'coord':r.end, 'position':'end'}
    s.commit()
    s.flush()
    return results

def get_regions_by_geneid_with_versions(s, geneid, panel_id):
    """
    gets all regions for gene

    :param s:
    :param geneid:
    :param panel_id:
    :return:
    """
    current_version = get_current_version(s, panel_id)
    sql = text("DROP TABLE IF EXISTS _versions;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _versions AS SELECT regions.id as r_id,
                    regions.chrom AS chrom,
                    regions.start AS region_start,
                    CASE WHEN (versions.panel_id = :panel_id AND versions.region_id = regions.id AND versions.extension_5 IS NOT NULL) THEN versions.extension_5
                        ELSE 0 END AS ext_5,
                    regions.end AS region_end,
                    CASE WHEN (versions.panel_id = :panel_id AND versions.region_id = regions.id AND versions.extension_3 IS NOT NULL) THEN versions.extension_3
                        ELSE 0 END AS ext_3,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM versions
                    JOIN regions ON versions.region_id = regions.id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    AND versions.panel_id = :panel_id
                    AND (versions.intro = :new_version OR (versions.intro <= :current_version AND (versions.last > :current_version OR versions.last IS NULL)))
                    GROUP BY regions.id ORDER BY region_start;""")

    values = {'panel_id': panel_id, 'gene_id': geneid, 'current_version': current_version,
              'new_version': current_version + 1}
    s.execute(sql, values)

    sql = text("""SELECT regions.id as region_id,
                        regions.chrom,
                        regions.start AS region_start,
                        0 AS ext_5,
                        regions."end" AS region_end,
                        0 AS ext_3,
                        group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                        FROM regions
                        JOIN exons ON regions.id = exons.region_id
                        JOIN tx ON tx.id = exons.tx_id
                        JOIN genes ON genes.id = tx.gene_id
                        WHERE genes.id = :gene_id
                        AND NOT EXISTS (SELECT * FROM _versions WHERE r_id = region_id)
                        GROUP BY regions.id
                        UNION
                        SELECT r_id AS region_id, chrom, region_start, ext_5, region_end, ext_3, name FROM _versions ORDER BY region_start;""")
    regions = s.execute(sql, values)
    s.flush()
    return list(regions)


def get_regions_by_geneid_with_versions_no_utr(s, geneid, panel_id):
    """

    :param s:
    :param geneid:
    :param panel_id:
    :return:
    """
    sql = text("DROP TABLE IF EXISTS _cds;")
    s.execute(sql)

    sql = text(
        """CREATE TEMP TABLE _cds AS
            SELECT regions.id as id, min(tx.cds_start) AS cds_start, max(tx.cds_end) AS cds_end
            FROM tx
            JOIN exons on tx.id = exons.tx_id
            JOIN regions ON exons.region_id = regions.id
            WHERE tx.gene_id = :gene_id
            GROUP BY regions.id;""")

    values = {'gene_id': geneid}
    s.execute(sql, values)
    current_version = get_current_version(s, panel_id)
    if not current_version:
        current_version = 0
    values = {'panel_id': panel_id, 'gene_id': geneid, 'current_version': current_version,
              'new_version': current_version + 1}

    sql = text("DROP TABLE IF EXISTS _versions_no_utr;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _versions_no_utr AS SELECT regions.id as r_id,
                    regions.chrom as chrom,
                    regions.start AS region_start,
                    CASE WHEN (versions.panel_id = :panel_id AND versions.region_id = regions.id AND versions.extension_5 IS NOT NULL) THEN versions.extension_5
                        ELSE 0 END AS ext_5,
                    regions.end AS region_end,
                    CASE WHEN (versions.panel_id = :panel_id AND versions.region_id = regions.id AND versions.extension_3 IS NOT NULL) THEN versions.extension_3
                        ELSE 0 END AS ext_3,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM versions
                    JOIN regions ON versions.region_id = regions.id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    AND versions.panel_id = :panel_id
                    AND (versions.intro = :new_version
                        OR
                        (versions.intro <= :current_version
                          AND
                            (versions.last > :current_version
                            OR
                            versions.last IS NULL)
                          )
                        )
                    GROUP BY regions.id ORDER BY region_start;""")
    s.execute(sql, values)

    sql = text("""SELECT regions.id as region_id,
                    regions.chrom,
                    regions.start AS region_start,
                    CASE WHEN (regions.start < (SELECT cds_start FROM _cds WHERE _cds.id = regions.id)) THEN regions.start - (SELECT cds_start FROM _cds WHERE _cds.id = regions.id) ELSE 0 END AS ext_5,
                    regions."end" AS region_end,
                    CASE WHEN (regions.end > (SELECT cds_end FROM _cds WHERE _cds.id = regions.id)) THEN (SELECT cds_end FROM _cds WHERE _cds.id = regions.id) - regions.end ELSE 0 END AS ext_3,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM regions
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    AND regions.end > (SELECT cds_start FROM _cds WHERE _cds.id = region_id)
                    AND regions.start < (SELECT tx.cds_end FROM _cds WHERE _cds.id = region_id)
                    AND NOT EXISTS (SELECT * FROM _versions_no_utr WHERE r_id = region_id)
                    GROUP BY regions.id
                    UNION
                    SELECT r_id AS region_id, chrom, region_start, ext_5, region_end, ext_3, name FROM _versions_no_utr ORDER BY region_start;""")
    regions = s.execute(sql, values)
    s.flush()
    return list(regions)


def get_regions_by_gene_no_utr(s, geneid):
    """

    :param s:
    :param geneid:
    :return:
    """
    sql = text("DROP TABLE IF EXISTS _cds_gene;")
    s.execute(sql)

    sql = text(
        "CREATE TEMP TABLE _cds_gene AS SELECT regions.id as id, min(tx.cds_start) AS cds_start, max(tx.cds_end) AS cds_end FROM tx JOIN exons on tx.id = exons.tx_id JOIN regions ON exons.region_id = regions.id WHERE tx.gene_id = :gene_id AND tx.cds_start != -1 GROUP BY regions.id;")
    values = {'gene_id': geneid}
    s.execute(sql, values)

    sql = text("""SELECT regions.id as region_id,
                    regions.chrom,
                    regions.start AS region_start,
                    CASE WHEN (regions.start < (SELECT cds_start FROM _cds_gene WHERE _cds_gene.id = regions.id)) THEN regions.start - (SELECT cds_start FROM _cds_gene WHERE _cds_gene.id = regions.id) ELSE 0 END AS ext_5,
                    regions."end" AS region_end,
                    CASE WHEN (regions.end > (SELECT cds_end FROM _cds_gene WHERE _cds_gene.id = regions.id)) THEN (SELECT cds_end FROM _cds_gene WHERE _cds_gene.id = regions.id) - regions.end ELSE 0 END AS ext_3,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM regions
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    AND regions.end > (SELECT cds_start FROM _cds_gene WHERE _cds_gene.id = region_id)
                    AND regions.start < (SELECT tx.cds_end FROM _cds_gene WHERE _cds_gene.id = region_id)
                    GROUP BY regions.id ORDER BY region_start;""")
    values = {'gene_id': geneid}
    regions = s.execute(sql, values)

    return list(regions)


def get_regions_by_geneid(s, geneid):
    """
    gets all regions for gene

    :param s:
    :param geneid:
    :param panel_id:
    :return:
    """
    sql = text("""SELECT regions.id as region_id,
                    regions.chrom,
                    regions.start AS region_start,
                    0 AS ext_5,
                    regions."end" AS region_end,
                    0 as ext_3,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM regions
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    GROUP BY regions.id ORDER BY region_start""")

    values = {'gene_id': geneid}
    regions = s.execute(sql, values)
    return list(regions)


def get_panel_regions_by_geneid(s, geneid, panelid):
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
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start ELSE regions.start - versions.extension_5 END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" ELSE regions."end" + versions.extension_3 END AS region_end,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM panels
                    JOIN versions ON versions.panel_id = panels.id
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = :panel_id AND genes.id = :gene_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL)
                    GROUP BY regions.id ORDER BY region_start""")
    values = {'panel_id': panelid, 'gene_id': geneid, 'version': current_version}
    regions = s.execute(sql, values)
    return list(regions)


def get_version_row(s, panel_id, region_id, current_version):
    """
    Gets the row from versions for a specific panel and region so the extension can be edited

    :param s:
    :param panel_id:
    :param region_id:
    :param current_version:
    :return:
    """
    versions = s.query(Versions). \
        filter(and_(Versions.panel_id == panel_id,
                    Versions.region_id == region_id,
                    or_(
                        and_(Versions.intro == current_version,
                             or_(Versions.last == None,
                                 Versions.last >= current_version)),
                        Versions.intro == current_version + 1),
                    or_(Versions.last >= current_version,
                        Versions.last == None)
                    )). \
        values(Versions.id, Versions.intro, Versions.last, Versions.extension_3, Versions.extension_5)
    for version in versions:
        return version


@message
def update_ext_query(s, version_id, panel_id=None, ext_3=None, ext_5=None, current_version=None, region_id=None):
    """
    If version row is in a live panel a new row is updated else just the relevant extension is updated.

    :param s:
    :param panel_id:
    :param version_id:
    :param ext:
    :param ext_type:
    :return:
    """
    if region_id:
        s.query(Versions).filter_by(id=version_id).update({Versions.last: current_version})
        v = Versions(intro=int(current_version) + 1, last=None, panel_id=panel_id, region_id=region_id,
                     extension_3=ext_3,
                     extension_5=ext_5, comment=None)
        s.add(v)
    else:
        s.query(Versions).filter_by(id=version_id).update({Versions.extension_5: ext_5, Versions.extension_3: ext_3})
    s.commit()
    return


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


def get_virtual_panels_simple(s):
    vpanels = s.query(VirtualPanels, VPRelationships, Versions, Panels). \
        group_by(VirtualPanels.name). \
        join(VPRelationships). \
        join(Versions). \
        join(Panels). \
        values(VirtualPanels.current_version, \
               VirtualPanels.name.label('vp_name'), \
               VirtualPanels.id,
               Panels.name.label('panel_name'),
               Panels.id.label('panelid'),
               Panels.locked,
               Panels.project_id.label('projectid'))

    return vpanels


def get_vpanel_by_id(s, vpanel_id, version=None):
    if not version:
        current_version = get_current_version_vp(s, vpanel_id)
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


def get_panel_details_by_id(s, panel_id):
    panel = s.query(Projects, Panels). \
        join(Panels). \
        filter(Panels.id == panel_id). \
        values(Panels.name, Panels.current_version)
    for p in panel:
        return p

def get_panel_id_by_name(s, panel_name):
    panels = s.query(Panels).filter(Panels.name == panel_name).values(Panels.id)
    for panel in panels:
        return panel.id

def get_vpanel_id_by_name(s, vpanel_name):
    panels = s.query(VirtualPanels).filter(VirtualPanels.name == vpanel_name).values(VirtualPanels.id)
    for panel in panels:
        return panel.id

def get_vpanel_name_by_id(s, vpanel_id):
    panels = s.query(VirtualPanels).filter(VirtualPanels.id == vpanel_id).values(VirtualPanels.name)
    for panel in panels:
        return panel.name

def get_vpanel_details_by_id(s, vpanel_id):
    panel = s.query(Projects, Panels, Versions, VPRelationships, VirtualPanels). \
        join(Panels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(VirtualPanels.id == vpanel_id). \
        values(VirtualPanels.name, VirtualPanels.current_version,
               Projects.name.label('project_name'), Projects.short_name.label('project_abv'), Projects.id.label('project_id'),
               Panels.name.label('panel_name'))
    for i in panel:
        print(i)
        return i


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

# todo edit this for new vp number format
@message
def remove_version_from_panel(s, panel_id, version_id):
    """
    Checks to see if region is live and if it is populates last, else removes from table
    Then checks vprelationships table and removes from virtual panels using the same logic

    :param s:
    :param panel_id:
    :param version_id:
    :return:
    """
    version = s.query(Versions).filter(Versions.region_id == version_id, Versions.panel_id == panel_id).all()
    current_version = get_current_version(s, panel_id)
    for v in version:
        if v.last == None:
            if v.intro > current_version: #if region is not live in the panel it cannot have been added to a virtual panel
                s.query(Versions).filter_by(id=v.id).delete()
            else:
                vp_relationships = s.query(VPRelationships).filter_by(version_id=v.id).all()
                for r in vp_relationships:
                    vp_version = get_current_version_vp(s, r.vpanel_id)
                    if r.intro > vp_version:
                        s.query(VPRelationships).filter_by(id=r.id).delete()
                    else:
                        s.query(VPRelationships).filter_by(id=r.id).update({VPRelationships.last: vp_version})
                s.query(Versions).filter_by(id=v.id).update({Versions.last: current_version})
    s.commit()
    return True


@message
def remove_version_from_vp(s, vp_id, version_id):
    """
    Checks to see if region is live and if it is populates last, else removes from table

    :param s:
    :param vp_id:
    :param version_id:
    :return:
    """
    vp_relationship = s.query(VPRelationships).filter(
        and_(VPRelationships.vpanel_id == vp_id, VPRelationships.version_id == version_id)).all()
    current_version = get_current_version_vp(s, vp_id)
    for r in vp_relationship:
        if r.intro > current_version:
            s.query(VPRelationships).filter_by(id=r.id).delete()
            s.commit()
        else:
            s.query(VPRelationships).filter_by(id=r.id).update({VPRelationships.last: current_version})
            s.commit()


@message
def make_panel_live(s, panelid, new_version, username):
    """
    makes a panel live

    :return: True
    :param s: db session
    :param panelid: panel id
    :param new_version: the new version number of the panel
    """
    project_id = get_project_id_by_panel_id(s, panelid)
    if check_user_has_permission(s, username, project_id):
        print('new_version')
        print(new_version)
        s.query(Panels).filter_by(id=panelid).update({Panels.current_version: new_version})
        s.commit()
        return True
    else:
        return False


@message
def make_vp_panel_live(s, vpanelid):
    """
    makes a virtual panel live

    :return: True
    :param s: db session
    :param vpanelid: panel id
    :param new_version: the new version number of the panel
    """
    panel_id = get_panel_by_vp_id(s, vpanelid)
    current_panel_version = get_current_version(s, panel_id)
    current_vpanel_version = get_current_version_vp(s, vpanelid)
    if current_panel_version > current_vpanel_version:
        new_version = float(current_panel_version) + 0.1
    else:
        new_version = float(current_vpanel_version) + 0.1

    s.query(VirtualPanels).filter_by(id=vpanelid).update({VirtualPanels.current_version: new_version})
    s.commit()

    return True


@message
def lock_panel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: user_id})
    s.commit()
    return True


def get_regions_by_panelid(s, panelid, version, extension=0):
    """
    Gets current regions for a given panel.
    Creates temp table containing custom regions and joins with all other regions.
    Table is sorted by chromosome and then region start.

    :param s:
    :param geneid:
    :param panelid:
    :return:
    """
    sql = text("DROP TABLE IF EXISTS _custom;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _custom AS SELECT versions.id AS version_id,
                       regions.chrom, panels.current_version, panels.name AS panel_name, '' AS gene_name,
                       CASE WHEN (versions.extension_5 IS NULL) THEN regions.start ELSE regions.start - versions.extension_5 END AS region_start,
                       CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" ELSE regions."end" + versions.extension_3 END AS region_end,
                       regions.name AS name
                       FROM panels
                       JOIN versions ON versions.panel_id = panels.id
                       JOIN regions ON regions.id = versions.region_id
                       WHERE panels.id = :panel_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL) AND regions.name IS NOT NULL""")
    values = {'panel_id': panelid, 'version': version}
    s.execute(sql, values)

    sql = text("SELECT * FROM _custom;")
    custom = s.execute(sql)
    if len(list(custom)) > 0:
        sql = text("""SELECT versions.id AS version_id,
                    regions.chrom, panels.current_version, panels.name AS panel_name, genes.name AS gene_name,
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start - :extension ELSE regions.start - versions.extension_5 - :extension END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" + :extension ELSE regions."end" + versions.extension_3 + :extension END AS region_end,
                    CASE WHEN regions.name IS NULL THEN group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) ELSE regions.name END AS name
                    FROM panels
                    JOIN versions ON versions.panel_id = panels.id
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = :panel_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL)
                    GROUP BY regions.id
                    UNION SELECT * FROM _custom
                    ORDER BY chrom,region_start;""")
    else:
        sql = text("""SELECT versions.id AS version_id,
                    regions.chrom, panels.current_version, panels.name AS panel_name, genes.name AS gene_name,
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start - :extension ELSE regions.start - versions.extension_5 - :extension END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" + :extension ELSE regions."end" + versions.extension_3 + :extension END AS region_end,
                    CASE WHEN regions.name IS NULL THEN group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) ELSE regions.name END AS name
                    FROM panels
                    JOIN versions ON versions.panel_id = panels.id
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = :panel_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL)
                    GROUP BY regions.id
                    ORDER BY chrom,region_start;""")
    values['extension'] = extension
    regions = s.execute(sql, values)
    return list(regions)


def get_genes_by_panelid_edit(s, panelid, current_version):
    genes = s.query(Genes, Tx, Exons, Regions, Versions, Panels). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(Panels). \
        filter(and_(Panels.id == panelid, or_(
        and_(Versions.intro <= current_version,
             or_(Versions.last == None,
                 Versions.last > current_version)),
        Versions.intro == current_version + 1),
                    or_(Versions.last >= current_version,
                        Versions.last == None))). \
        values(Genes.name, \
               Genes.id)
    return genes


def get_regions_by_vpanelid(s, vpanelid, version, extension=0):
    """
    Creates temporary table containing custom regions then selects all regions for virtual panels and combines with custom regions.
    Table is sorted by chrom then region start.

    :param s:
    :param vpanelid:
    :param version:
    :return:
    """
    if type(version) == float or type(version) == Decimal:
        version = round(version, 1)

    sql = text("DROP TABLE IF EXISTS _custom;")
    s.execute(sql)

    sql = text("""CREATE TEMP TABLE _custom AS SELECT versions.id AS version_id,
                regions.chrom, virtual_panels.current_version, virtual_panels.name AS panel_name, 'N/A' AS gene_name,
                CASE WHEN (versions.extension_5 IS NULL) THEN regions.start ELSE regions.start - versions.extension_5 END AS region_start,
                CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" ELSE regions."end" + versions.extension_3 END AS region_end,
                regions.name AS name
                FROM virtual_panels
                JOIN VP_relationships on virtual_panels.id = VP_relationships.vpanel_id
                JOIN versions on VP_relationships.version_id = versions.id
                JOIN regions ON regions.id = versions.region_id
                WHERE virtual_panels.id = :vpanel_id AND VP_relationships.intro <= :version AND (VP_relationships.last >= :version OR VP_relationships.last IS NULL)
                AND regions.name IS NOT NULL;
                """)
    values = {'vpanel_id': vpanelid, 'version': version}
    s.execute(sql, values)

    sql = text("""SELECT versions.id AS version_id,
                regions.chrom, virtual_panels.current_version, virtual_panels.name AS panel_name, genes.name AS gene_name,
                CASE WHEN (versions.extension_5 IS NULL) THEN regions.start - :extension ELSE regions.start - versions.extension_5  - :extension END AS region_start,
                CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" + :extension ELSE regions."end" + versions.extension_3 + :extension END AS region_end,
                CASE WHEN regions.name IS NULL THEN group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) ELSE regions.name END AS name
                FROM virtual_panels
                JOIN VP_relationships on virtual_panels.id = VP_relationships.vpanel_id
                JOIN versions on VP_relationships.version_id = versions.id
                JOIN regions ON regions.id = versions.region_id
                JOIN exons ON regions.id = exons.region_id
                JOIN tx ON tx.id = exons.tx_id
                JOIN genes ON genes.id = tx.gene_id
                WHERE virtual_panels.id = :vpanel_id AND VP_relationships.intro <= :version AND (VP_relationships.last >= :version OR VP_relationships.last IS NULL)
                GROUP BY regions.id
                UNION SELECT * FROM _custom
                ORDER BY chrom,region_start;""")
    values["extension"] = extension
    regions = s.execute(sql, values)
    return list(regions)


def get_genes_by_vpanelid_edit(s, vpanel_id, current_version):
    """


    :param s:
    :param vpanel_id:
    :param current_version:
    :return:
    """
    genes = s.query(Genes, Tx, Exons, Regions, Versions, VPRelationships, VirtualPanels). \
        join(Tx). \
        join(Exons). \
        join(Regions). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(and_(VirtualPanels.id == vpanel_id,
                    or_(
                        and_(VPRelationships.intro <= current_version,
                             or_(VPRelationships.last == None,
                                 VPRelationships.last >= current_version)),
                        VPRelationships.intro == float(current_version) + 0.1),
                    or_(VPRelationships.last >= current_version,
                        VPRelationships.last == None))). \
        distinct(Genes.name). \
        group_by(Genes.name). \
        values(Genes.name, Genes.id)

    return genes

def get_gene_cds(s, region_id):
    """
    Method to get the cds co-ordinates for the gene given a region ID

    :param s: SQLAlchemy session token
    :param region_id: ID of teh region of interest
    :return:
    """
    sql = text("""SELECT min(tx.cds_start) AS cds_start, max(tx.cds_end) AS cds_end 
                    FROM tx 
                    JOIN exons on tx.id = exons.tx_id 
                    JOIN regions ON exons.region_id = regions.id 
                    WHERE regions.id = :region_id
                    GROUP BY regions.id;
                """)
    values = {"region_id":region_id}
    result = s.execute(sql, values)
    for i in result:
        return i

def add_testcode(s, vpanel_id, version, testcode):
    """
    Method to add a new row to the testcodes table (required for API methods to link to StarLIMS)

    :param s:
    :param vpanel_id:
    :param version:
    :param testcode:
    :return:
    """
    tc = TestCodes(vpanel_id, version, testcode)
    s.add(tc)
    s.commit()
    return tc.id
