from app.queries import *
from sqlalchemy import and_, or_, case
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
def create_virtualpanel_query(s, name):
    """
    creates a virtual panel in the virtual panels table and adds the vp_relationship to the broad panel

    :param s: db session
    :param name: name of virtual panel
    :return: virtual panel id
    """
    try:
        virtualpanel = VirtualPanels(name, 0)
        s.add(virtualpanel)
        s.commit()
        return virtualpanel.id
    except exc.IntegrityError:
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
    print(ext_3)
    print(ext_5)
    version = Versions(intro=int(current) + 1, last=None, panel_id=panelid, region_id=regionid, comment=None,
                       extension_3=ext_3, extension_5=ext_5)
    s.add(version)
    print(version.extension_5)
    # s.commit()
    return version.id

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

    :param s:
    :param vp_id:
    :param version_id:
    :return:
    """
    vp_relationship = VPRelationships(intro=1, last=None, version_id=version_id, vpanel_id=vp_id)
    s.add(vp_relationship)
    s.commit()
    return vp_relationship.id

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
    print(region.id)
    version_id = add_region_to_panel(s, region.id, panel_id)
    s.commit()
    return region.id , version_id

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
    chrom_order = case(((Regions.chrom == 'chr1',1),(Regions.chrom == 'chr2',2),(Regions.chrom == 'chr3',3),
                        (Regions.chrom == 'chr4',4),(Regions.chrom == 'chr5',5),(Regions.chrom == 'chr6',6),
                        (Regions.chrom == 'chr7',7),(Regions.chrom == 'chr8',8),(Regions.chrom == 'chr9',9),
                        (Regions.chrom == 'chr10',10),(Regions.chrom == 'chr11',11),(Regions.chrom == 'chr12',12),
                        (Regions.chrom == 'chr13',13),(Regions.chrom == 'chr14',14),(Regions.chrom == 'chr15',15),
                        (Regions.chrom == 'chr16',16),(Regions.chrom == 'chr17',17),(Regions.chrom == 'chr18',18),
                        (Regions.chrom == 'chr19',19),(Regions.chrom == 'chr20',20),(Regions.chrom == 'chr21',21),
                        (Regions.chrom == 'chr22',22),(Regions.chrom == 'chrX',23),(Regions.chrom == 'chrY',24)))
    current_version = get_current_version(s, panelid)
    print(current_version)
    custom_regions = s.query(Versions, Regions).join(Regions).\
        filter(and_(Versions.panel_id == panelid,
                    or_(
                        and_(Versions.intro == current_version, Versions.last != current_version + 1),
                        Versions.intro == current_version + 1),
                    or_(Versions.last >= current_version, Versions.last == None),
                    Regions.name.isnot(None))). \
        order_by(chrom_order, Regions.start).\
        values(Versions.id.label("version_id"), Regions.id.label("region_id"), Regions.chrom,
               case([(Versions.extension_5 == None, Regions.start)], else_=Regions.start+Versions.extension_5).label('region_start'),
               case([(Versions.extension_3 == None, Regions.end)], else_=Regions.end+Versions.extension_3).label('region_end'),
               Regions.name)

    return custom_regions

def get_current_custom_regions(s, vpanel_id):
    """
    Gets custom regions currently included in panel

    :param s:
    :param vpanel_id:
    :return:
    """
    ids = s.query(VPRelationships, Versions, Regions).\
        join(Versions).\
        join(Regions).\
        group_by(Versions.id).\
        filter(and_(VPRelationships.vpanel_id == vpanel_id, Regions.name.isnot(None))).\
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
    versions = s.query(VPRelationships, Versions, Regions, Exons, Tx).\
        join(Versions).\
        join(Regions).\
        join(Exons).\
        join(Tx).\
        filter(and_(Tx.gene_id == gene_id, VPRelationships.vpanel_id == vp_id,
                    or_(
                        and_(VPRelationships.intro == current_version, VPRelationships.last != current_version + 1),
                        VPRelationships.intro == current_version + 1),
                    or_(VPRelationships.last >= current_version, VPRelationships.last == None))).\
        group_by(VPRelationships.id).\
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
    versions = s.query(Versions, Regions, Exons, Tx).\
        join(Regions).\
        join(Exons).\
        join(Tx).\
        filter(and_(Tx.gene_id == gene_id, Versions.panel_id == panel_id,
                    or_(
                        and_(Versions.intro <= current_version, Versions.last != current_version + 1),
                        Versions.intro == current_version + 1),
                    or_(Versions.last >= current_version, Versions.last == None))).\
        group_by(Versions.id).\
        values(Regions.id)
    print(str(versions))
    return versions

def get_panel_by_vp_id(s, vp_id):
    panel = s.query(VirtualPanels, VPRelationships, Versions).join(VPRelationships).join(Versions).distinct(Versions.panel_id).group_by(Versions.panel_id).filter(VirtualPanels.id==vp_id).values(Versions.panel_id)
    for i in panel:
        return i.panel_id

def get_regions_by_geneid_with_versions(s, geneid, panel_id):
    """
    gets all regions for gene

    :param s:
    :param geneid:
    :param panel_id:
    :return:
    """
    sql = text("""SELECT regions.id as region_id,
                    regions.chrom,
                    CASE WHEN (versions.panel_id = :panel_id AND versions.region_id = regions.id AND versions.extension_5 IS NOT NULL) THEN regions.start - versions.extension_5 ELSE regions.start END AS region_start,
                    CASE WHEN (versions.panel_id = :panel_id AND versions.region_id = regions.id AND versions.extension_3 IS NOT NULL) THEN regions."end" + versions.extension_3 ELSE regions."end" END AS region_end,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM versions
                    JOIN regions ON versions.region_id = regions.id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = :gene_id
                    GROUP BY regions.id ORDER BY region_start""")

    values = {'panel_id': panel_id, 'gene_id': geneid}
    print('starting')
    regions = s.execute(sql, values)
    print('returning')
    return regions

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
                    regions."end" AS region_end,
                    group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM regions
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE genes.id = 837
                    GROUP BY regions.id ORDER BY region_start""")

    values = {'gene_id': geneid}
    print('starting')
    regions = s.execute(sql, values)
    print('returning')
    return regions

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
                    FROM panels, versions
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = :panel_id AND genes.id = :gene_id AND versions.intro <= :version AND (versions.last >= :version OR versions.last IS NULL)
                    GROUP BY regions.id ORDER BY region_start""")
    values = {'panel_id':panelid, 'gene_id':geneid, 'version':current_version}
    regions = s.execute(sql, values)
    return regions

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

    return panel

def get_vpanel_details_by_id(s, vpanel_id):
    panel = s.query(Projects, Panels, Versions, VPRelationships, VirtualPanels). \
        join(Panels). \
        join(Versions). \
        join(VPRelationships). \
        join(VirtualPanels). \
        filter(VirtualPanels.id == vpanel_id). \
        values(VirtualPanels.name, VirtualPanels.current_version, Projects.id.label('project_id'))
    for i in panel:
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

@message
def remove_version_from_panel(s, panel_id, version_id):
    """
    Checks to see if region is live and if it is populates last, else removes from table
    Then checks vprelationships table and removes from virtual panels

    :param s:
    :param panel_id:
    :param version_id:
    :return:
    """
    version = s.query(Versions).filter_by(id=version_id).all()
    current_version = get_current_version(s, panel_id)
    for v in version:
        if v.intro > current_version:
            s.query(Versions).filter_by(id=v.id).delete()
        else:
            vp_relationships = s.query(VPRelationships).filter_by(version_id=v.id).all()
            for r in vp_relationships:
                if v.intro > current_version:
                    s.query(VPRelationships).filter_by(id=r.id).delete()
                else:
                    vp_version = get_current_version_vp(s, r.vpanel_id)
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
    vp_relationship = s.query(VPRelationships).filter(and_(VPRelationships.vpanel_id == vp_id, VPRelationships.version_id == version_id)).all()
    current_version = get_current_version_vp(s, vp_id)
    for r in vp_relationship:
        print(r.id)
        print(r.intro)
        if r.intro > current_version:
            s.query(VPRelationships).filter_by(id=r.id).delete()
            s.commit()
        else:
            s.query(VPRelationships).filter_by(id=r.id).update({VPRelationships.last: current_version})
            s.commit()


@message
def make_panel_live(s, panelid, new_version, username):
    """
    makes a panel line

    :return: True
    :param s: db session
    :param panelid: panel id
    :param new_version: the new version number of the panel
    """
    project_id = get_project_id_by_panel_id(s, panelid)
    if check_user_has_permission(s, username, project_id):
        s.query(Panels).filter_by(id=panelid).update({Panels.current_version: new_version})
        s.commit()
        return True
    else:
        return False

@message
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

@message
def lock_panel(s, username, panel_id):
    user_id = get_user_id_by_username(s, username)
    lock = s.query(Panels).filter_by(id=panel_id).update(
        {Panels.locked: user_id})
    s.commit()
    return True

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
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start ELSE regions.start - versions.extension_5 END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" ELSE regions."end" + versions.extension_3 END AS region_end,
                    CASE WHEN regions.name IS NULL THEN group_concat(DISTINCT tx.accession || "_exon" || CAST(exons.number AS VARCHAR)) ELSE regions.name END AS name
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
