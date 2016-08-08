import json
import sqlite3
from enum import Enum
import os
from pybedtools import BedTool

from app import models


class Database():
    def __init__(self):
        path = os.path.dirname(__file__)
        self.refflat = path + '/resources/refflat.db'
        self.refflat_conn = sqlite3.connect(self.refflat,check_same_thread=False)
        self.panelpal = path + '/resources/panel_pal.db'
        self.panelpal_conn = sqlite3.connect(self.panelpal,check_same_thread=False)
        pp = self.panelpal_conn.cursor()
        pp.execute('ATTACH database ? as rf;', (self.refflat,))
        pp.close()

    def delete(self,conn, table, id):
        pp = conn.cursor()
        print table
        print id
        query = "DELETE FROM " + table + " WHERE id = ?"
        print query
        projects = pp.execute(query, (id,))
        conn.commit()
        print projects

    def query_db(self,c, query, args=(), one=False):
        """

        general method to do a select statement and format result into an easy to use dict

        :param c:
        :param query:
        :param args:
        :param one:
        :return: list of dicts
        """
        c.execute(query, args)
        r = [dict((c.description[i][0], value) \
                  for i, value in enumerate(row)) for row in c.fetchall()]
        return (r[0] if r else None) if one else r

    def __del__(self):
        self.panelpal_conn.commit()
        self.panelpal_conn.close()
        self.refflat_conn.commit()
        self.refflat_conn.close()


class Projects(Database):
    def query_db(self, c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def add_project(self ,project):
        pp = self.panelpal_conn.cursor()
        try:
            pp.execute("INSERT OR IGNORE INTO projects(name) VALUES (?)", (project,))
            self.panelpal_conn.commit()
            return pp.lastrowid
        except self.panelpal_conn.Error as e:
            self.panelpal_conn.rollback()
            print e.args[0]
            return -1

    def get_project(self, project):
        pp = self.panelpal_conn.cursor()
        projects = self.query_db(pp, "SELECT id FROM projects WHERE name=?", (project,))
        if len(projects) == 0:
            project_id = self.add_project(project)
        else:
            project_id = projects[0].get('id')

        return project_id

    def get_projects(self):
        pp = self.panelpal_conn.cursor()
        projects = self.query_db(pp, "SELECT * FROM projects")

        return projects

class Studies(Database):
    def query_db(self, c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def add_study(self, study, project_id):
        pp = self.panelpal_conn.cursor()
        try:
            pp.execute("INSERT OR IGNORE INTO studies(name, project_id, current_version) VALUES (?,?,1)", (study,project_id))
            self.panelpal_conn.commit()
            return pp.lastrowid
        except self.panelpal_conn.Error as e:
            self.panelpal_conn.rollback()
            print e.args[0]
            return -1

    def get_study(self, study):
        pp = self.panelpal_conn.cursor()
        try:
            study_id = self.query_db(pp, "SELECT id FROM studies WHERE name = ?", (study,))[0].get('id')
            return study_id
        except IndexError:
            return -1


class Panels(Database):

    def query_db(self,c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def add_panel(self,panel, project_id, conn):
        pp = conn.cursor()
        try:
            pp.execute("INSERT OR IGNORE INTO panels(name, study_id) VALUES (?, ?)", (panel,project_id))
            conn.commit()
            return pp.lastrowid
        except conn.Error as e:
            conn.rollback()
            print e.args[0]
            return -1


    def get_panel_id(self ,panel, team_id):
        pp = self.panelpal_conn.cursor()
        panels = self.query_db(pp, "SELECT id FROM panels WHERE name=?", (panel,))
        if len(panels) == 0:
            panel_id = self.add_panel(panel, team_id, self.panelpal_conn)
        else:
            panel_id = panels[0].get('id')
        pp.close()
        return panel_id

    def get_panels(self):
        pp = self.panelpal_conn.cursor()
        panels = self.query_db(pp, "SELECT panels.name as panelname,studies.name as projectname, studies.current_version, panels.id as panelid FROM panels join studies on panels.study_id = studies.id ")
        return panels


    def get_panel(self,id):
        pp = self.panelpal_conn.cursor()

        panel_info = self.query_db(pp, 'SELECT id, current_version FROM panels WHERE id = ?', (id,))
        panel_id = panel_info[0].get('id')
        panel_v = panel_info[0].get('current_version')

        panel = self.query_db(pp,
                              'SELECT panels.id as panelid, panels.current_version, panels.name as panelname, versions.intro,versions.last,versions.region_id, versions.id, genes.name as genename, regions.chrom, regions.start, regions.end, versions.extension_3, versions.extension_5, tx.accession FROM versions join regions on regions.id=versions.region_id join exons on regions.id=exons.region_id join tx on exons.tx_id = tx.id join genes on tx.gene_id = genes.id join panels on versions.panel_id = panels.id  WHERE panel_id = ? AND intro <= ? AND (last >= ? OR last ISNULL)',
                              (panel_id, panel_v, panel_v))
        return panel

    def add_to_version(self,panel_id, region_id, version, extension_3, extension_5):
        pp=self.panelpal_conn.cursor()
        command = 'INSERT INTO versions(intro, panel_id, region_id'
        values = 'VALUES(?,?,?'
        versions = [version, panel_id, region_id]
        if extension_3 is not None:
            command += ', extension_3'
            values += ', ?'
            versions.append(extension_3)
        if extension_5 is not None:
            command += ', extension_5'
            values += ', ?'
            versions.append(extension_5)
        command = command + ') ' + values + ')'
        try:
            pp.execute(command, versions)
            self.panelpal_conn.commit()
            return 0
        except self.panelpal_conn.Error as e:
            self.panelpal_conn.rollback()
            print 'Error'
            print e.args
            return -1

    def insert_versions(self,genes, panel_id, version, use_cds):
        pp = self.panelpal_conn.cursor()
        current_regions = []
        current = self.query_db(pp, "SELECT region_id FROM versions WHERE panel_id=?;", (panel_id,))
        if len(current) > 0:
            for c in current:
                current_regions.append(c.get('region_id'))
        current_regions = set(current_regions)

        for gene in genes:
            results = self.query_db(pp,
                               '''SELECT regions.id, regions.start, regions.end, tx.strand, tx.cds_start, tx.cds_end
                                    FROM genes
                                    JOIN tx ON genes.id=tx.gene_id
                                    JOIN exons ON tx.id=exons.tx_id
                                    JOIN regions ON exons.region_id=regions.id
                                    WHERE name = ?
                                    ORDER BY start''',
                               (gene,))
            regions = {}
            for r in results:
                r_id = r.get('id')
                r_start = r.get('start')
                r_end = r.get('end')
                cds_start = r.get('cds_start')
                cds_end = r.get('cds_end')
                tx = {'cds_start':cds_start, 'cds_end':cds_end}
                if r_id not in regions:
                    regions[r_id] = {'start':r_start, 'end':r_end, 'tx':[tx]}
                elif tx not in regions[r_id]['tx']:
                    regions[r_id]['tx'].append(tx)
            for region in regions:
                if region not in current_regions and use_cds:
                    region_start = regions[region].get('start')
                    region_end = regions[region].get('end')
                    #get longest cds coordinates for gene
                    gene_cds_start = 400000000
                    gene_cds_end = 0
                    for tx in regions[region].get('tx'):
                        if tx.get('cds_start') < gene_cds_start:
                            gene_cds_start = tx.get('cds_start')
                        if tx.get('cds_end') > gene_cds_end:
                            gene_cds_end = tx.get('cds_end')
                    #add extensions to region to exclude UTRs when exporting BED
                    if gene_cds_start > region_end or gene_cds_end < region_start:
                        pass
                    elif region_start < gene_cds_start < region_end:
                        extension_5 = region_start - gene_cds_start #negative number required
                        self.add_to_version(panel_id, region, version, None, extension_5)
                    elif region_start < gene_cds_end < region_end:
                        extension_3 = gene_cds_end - region_end #negative number required
                        self.add_to_version(panel_id, region, version, extension_3, None)
                    else:
                        self.add_to_version(panel_id, region, version, None, None)
                #if UTRs are required, just add region to versions table
                elif region not in current_regions:
                    self.add_to_version(panel_id, region, version, None, None)

    def import_bed(self, study, panel, gene_file, bed_file, use_cds=True):

        f = open(gene_file, 'r')
        genes = [line.strip('\n') for line in f.readlines()]

        s = Studies()
        project_id = s.get_study(study)
        print study + " id = " + str(project_id)
        if project_id == -1:
            print 'Could not insert project ' + study + "; exiting."
            exit()
        panel_id = self.get_panel_id(panel, project_id)
        print panel + " id = " + str(panel_id)
        if panel_id == -1:
            print 'Could not insert panel ' + panel + "; exiting."
            exit()

        pp = self.panelpal_conn.cursor()
        version = self.query_db(pp, 'SELECT current_version FROM studies WHERE id = ?', (project_id,))
        pp.close()
        self.insert_versions(genes, panel_id, version[0].get('current_version'), use_cds)

        pp_bed = self.export_bed(panel, 'ROI_25')
        self.compare_bed(bed_file, False, pp_bed)




    def import_pref_transcripts(self, project, transcripts):
        f = open(transcripts, 'r')
        tx_list = [line.strip('\n') for line in f.readlines()]

        pp = self.panelpal_conn.cursor()
        project_id = self.query_db(pp, 'SELECT id fROM projects WHERE name = ?', (project,))[0].get('id')

        for tx in tx_list:
            if tx != tx_list[0]:
                acc = tx.split('\t')[1].split('.')[
                    0]  # splits gene name from transcript and removes version from accession
                try:
                    tx_id = self.query_db(pp, 'SELECT id FROM tx WHERE accession = ?', (acc,))[0].get('id')
                    pp.execute('INSERT INTO pref_tx (project_id, tx_id) VALUES (?,?)', (project_id, tx_id))
                except IndexError:
                    print acc + ' not in refflat database'

    def export_bed(self, panel, bed_type):
        pp = self.panelpal_conn.cursor()

        panel_info = self.query_db(pp, 'SELECT panels.id, study_id, studies.project_id, studies.current_version FROM panels JOIN studies ON panels.study_id = studies.id WHERE panels.name = ?', (panel,))[0]
        panel_id = panel_info.get('id')
        panel_v = panel_info.get('current_version')
        study_id = panel_info.get('study_id')
        project_id = panel_info.get('project_id')


        whole_project = False
        if bed_type == "ROI_5":
            extension = 5
        elif bed_type == "ROI_25":
            extension = 25
        elif bed_type == "Project":
            extension = 25
            whole_project = True
        else:
            return "BED type not valid. Please use ROI_5, ROI_25 or Project."

        print extension

        if whole_project:
            regions = self.query_db(pp,
                                    '''SELECT versions.region_id, regions.chrom,
                                          CASE WHEN versions.extension_5 ISNULL THEN regions.start - ? ELSE regions.start - versions.extension_5 - ? END as start,
                                          CASE WHEN versions.extension_3 ISNULL THEN regions.end + ? ELSE regions.end + versions.extension_3 + ? END as end, tx.accession,
                                          "ex" || exons.number || "_" || genes.name || "_" || tx.accession  as identifier
                                          FROM versions
                                          JOIN panels ON panels.id = versions.panel_id
                                          JOIN regions ON regions.id = versions.region_id
                                          JOIN exons ON exons.region_id = regions.id
                                          JOIN tx ON exons.tx_id = tx.id
                                          JOIN genes ON tx.gene_id = genes.id
                                          WHERE panels.study_id = ? AND intro <= ? AND (last >= ? OR last ISNULL)''',
                                    (extension, extension, extension, extension, study_id, panel_v, panel_v))
        else:
            regions = self.query_db(pp,
                              '''SELECT versions.region_id, regions.chrom,
                                    CASE WHEN versions.extension_5 ISNULL THEN regions.start - ? ELSE regions.start - versions.extension_5 - ? END as start,
                                    CASE WHEN versions.extension_3 ISNULL THEN regions.end + ? ELSE regions.end + versions.extension_3 + ? END as end, tx.accession,
                                    "ex" || exons.number || "_" || genes.name || "_" || tx.accession  as identifier
                                    FROM versions
                                    JOIN panels ON panels.id = versions.panel_id
                                    JOIN regions ON regions.id = versions.region_id
                                    JOIN exons ON exons.region_id = regions.id
                                    JOIN tx ON exons.tx_id = tx.id
                                    JOIN genes ON tx.gene_id = genes.id
                                    WHERE versions.panel_id = ? AND intro <= ? AND (last >= ? OR last ISNULL)''',
                               (extension, extension, extension, extension, panel_id, panel_v, panel_v))

        formatted_result = {}

        for region in regions:
            region_start = region.get('start')
            region_end = region.get('end')
            c = region.get('chrom')

            if c not in formatted_result:
                formatted_result[c] = {}
            if region_start not in formatted_result[c]:
                formatted_result[c][region_start] = {}
            if region_end not in formatted_result[c][region_start]:
                formatted_result[c][region_start][region_end] = {}
            if "accession" not in formatted_result[c][region_start][region_end]:
                formatted_result[c][region_start][region_end]["accession"] = []

            accession = {'name':region.get('accession'), 'identifier':region.get('identifier')}
            formatted_result[c][region_start][region_end]["accession"].append(accession)


        main_tx_result = self.query_db(pp, '''SELECT tx.accession
                                            FROM pref_tx
                                            JOIN tx ON tx.id = pref_tx.tx_id
                                            WHERE pref_tx.project_id = ?''', (project_id,))

        master_accessions = []
        for tx in main_tx_result:
            master_accessions.append(tx.get('accession'))

        lines = []
        for chrom in formatted_result:
            for start in formatted_result[chrom]:
                for end in formatted_result[chrom][start]:
                    accessions = formatted_result[chrom][start][end]['accession']
                    if len(accessions) > 1:
                        for acc in accessions:
                            name = acc["name"]

                            if name in master_accessions:
                                ident = "*" + acc["identifier"] + "*"
                            else:
                                ident = acc["identifier"]
                            out = [chrom, start, end, ident]
                            line = "\t".join(str(x) for x in out)
                            lines.append(line)
                    elif len(accessions) == 1:
                        acc = accessions[0]
                        ident = acc["identifier"]
                        out = [chrom, start, end, ident]
                        line = "\t".join(str(x) for x in out)
                        lines.append(line)
        sorted_lines = sorted(lines)

        bed = "\n".join(sorted_lines)
        merged_bed = self.check_bed(bed, True)
        return merged_bed


    def get_panel_by_project(self,project):
        pass

    def check_bed(self, bed_file, stream):
        bed = BedTool(bed_file, from_string=stream)
        try:
            sorted_bed = bed.sort()
            merged_bed = sorted_bed.merge(c="4", o="distinct")

            return merged_bed

        except Exception as exception:
            print ("ERROR: " + str(exception))

    def compare_bed(self, bed_file, orig_from_string, pp_bed):
        original_bed = BedTool(bed_file, from_string=orig_from_string)

        missing_from_pp = original_bed.intersect(pp_bed, v=True)
        print 'Missing from exported BED'
        print missing_from_pp
        missing_from_orig = pp_bed.intersect(original_bed, v=True)
        print 'Missing from original BED'
        print missing_from_orig


    # TODO merge with develop_matt to change version update
    def remove_gene(self,panel_id,gene):
        pp = self.panelpal_conn.cursor()
        panel = self.get_panel(int(panel_id))
        ids=[]
        current_version=0
        for i in panel:
            if i["genename"] == gene:
                id = i["id"]
                intro = i["intro"]
                current_version = i["current_version"]
                pp.execute('UPDATE versions SET last = ? WHERE id = ?',(current_version,id,))
                ids.append(id)
        new_version = current_version+1
        pp.execute('UPDATE panels SET current_version = ? WHERE id = ?',(new_version,panel_id,))
        self.panelpal_conn.commit()

class Users(Database):
    def query_db(self, c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def get_users(self):
        # pp = self.panelpal_conn.cursor()
        # users = self.query_db(pp,"SELECT * FROM users")
        # return users
        print models.Users.query.all()

    def add_user(self,user):
        pp = self.panelpal_conn.cursor()
        try:
            pp.execute("INSERT OR IGNORE INTO users(username) VALUES (?)", (user,))
            self.panelpal_conn.commit()
            return pp.lastrowid
        except self.panelpal_conn.Error as e:
            self.panelpal_conn.rollback()
            print e.args[0]
            return -1

class Regions(Database):
    def query_db(self, c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def get_regions_by_gene(self,gene):

        c = self.refflat_conn.cursor()
        result = self.query_db(c,"SELECT * FROM genes join tx on genes.id=tx.gene_id join exons on tx.id = exons.tx_id join regions on exons.region_id = regions.id WHERE name=?", (gene,))
        formatted_result = {}
        formatted_result[gene] = {}

        for region in result:
            print json.dumps(region,indent=4)
            tx = region["accession"]
            exon_id = region["id"]
            number = region["number"]
            chrom = region["chrom"]
            strand = region["strand"]
            start = region["start"]
            end = region["end"]
            formatted_result[gene]["chrom"]=chrom
            if tx not in formatted_result[gene]:
                formatted_result[gene][tx]={}
            formatted_result[gene][tx]["strand"] = strand
            if "exons" not in formatted_result[gene][tx]:
                formatted_result[gene][tx]["exons"]=[]

            exon_details = {"id": exon_id, "start": start, "end": end, "number": number}
            formatted_result[gene][tx]["exons"].append(exon_details)

        return formatted_result

    def get_regions_by_tx(self, tx):
        c = self.refflat_conn.cursor()
        result = self.query_db(c,
                          "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE accession=?",
                          (tx,))
        formatted_result = {}
        formatted_result[tx] = {}
        for region in result:
            name = region["name"]
            tx = region["accession"]
            exon_id = region["id"]
            chrom = region["chrom"]
            strand = region["strand"]
            start = region["start"]
            end = region["end"]
            number = region["number"]
            formatted_result[tx]["chrom"] = chrom
            formatted_result[tx]["gene"] = name
            formatted_result[tx]["strand"] = strand
            if "exons" not in formatted_result[tx]:
                formatted_result[tx]["exons"] = []
            exon_details = {"id": exon_id, "start": start, "end": end, "number":number}
            formatted_result[tx]["exons"].append(exon_details)



        return formatted_result

    def genes_in_region(self,chrom,start,end):
        # TODO will only get if exon is in region need to do introns too
        c = self.refflat_conn.cursor()
        fully_within = self.query_db(c,
                          "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE chrom=? AND (start >= ? AND end <= ?)",
                          (chrom,start,end,))
        x = self.query_db(c,
                                "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE chrom=? AND (start <= ? AND end >= ?)",
                                (chrom, start,start,))
        y = self.query_db(c,
                                "SELECT * FROM tx join genes on tx.gene_id=genes.id join exons on tx.id = exons.tx_id WHERE chrom=? AND (start <= ? AND end >=  ?)",
                                (chrom, end,end,))

        c.connection.close()

        return fully_within + x + y



#users= models.Users.query.all()
#print users
#for u in users:
#    print(u.id,u.username)
#    print u.id
#    print u.username

#Panels().import_bed('NGD', 'HSPRecessive', '/home/bioinfo/Natalie/wc/genes/NGD_HSPrecessive_v1.txt', '/results/Analysis/MiSeq/MasterBED/NGD_HSPrecessive_v1.bed', True)
#bed = p.check_bed('/home/bioinfo/Natalie/wc/genes/test.bed')
#print bed