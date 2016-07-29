import sqlite3
import argparse
import json
import os
from pybedtools import BedTool


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
            project_id = self.add_project(project, self.panelpal_conn)
        else:
            project_id = projects[0].get('id')

        return project_id

    def get_projects(self):
        pp = self.panelpal_conn.cursor()
        projects = self.query_db(pp, "SELECT * FROM projects")

        return projects

class Panels(Database):

    def query_db(self,c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def add_panel(self,panel, project_id, conn):
        pp = conn.cursor()
        try:
            pp.execute("INSERT OR IGNORE INTO panels(name, team_id, current_version) VALUES (?, ?, 1)", (panel,project_id))
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
        panels = self.query_db(pp, "SELECT panels.name as panelname,projects.name as projectname, current_version, panels.id as panelid FROM panels join projects on panels.team_id = projects.id ")
        return panels


    def get_panel(self,id):
        pp = self.panelpal_conn.cursor()

        panel_info = self.query_db(pp, 'SELECT id, current_version FROM panels WHERE id = ?', (id,))
        panel_id = panel_info[0].get('id')
        panel_v = panel_info[0].get('current_version')

        panel = self.query_db(pp,
                              'SELECT rf.genes.name as genename, rf.regions.chrom, rf.regions.start, rf.regions.end, versions.extension_3, versions.extension_5, rf.tx.accession FROM versions join regions on rf.regions.id=versions.region_id join rf.exons on rf.regions.id=rf.exons.region_id join rf.tx on rf.exons.tx_id = rf.tx.id join rf.genes on rf.tx.gene_id = rf.genes.id  WHERE panel_id = ? AND intro <= ? AND (last >= ? OR last ISNULL)',
                              (panel_id, panel_v, panel_v))
        return panel

    def add_to_version(self,panel_id, region_id, version, extension_3, extension_5):
        pp=self.panelpal_conn.cursor()
        command = 'INSERT INTO versions(intro, panel_id, region_id'
        values = 'VALUES(?,?,?'
        versions = (version, panel_id, region_id)
        if extension_3 is not None:
            command += ', extension_3'
            values += ', ?'
            versions.extend(extension_3)
        if extension_5 is not None:
            command += ', extension_5'
            values += ', ?'
            versions.extend(extension_5)
        command = command + ') ' + values + ')'
        try:
            pp.execute(command, versions)
            self.panelpal_conn.commit()
            return 0
        except self.panelpal_conn.Error as e:
            self.panelpal_conn.rollback()
            print e.args[0]
            return -1

    def insert_versions(self,genes, panel_id, version):
        pp = self.panelpal_conn.cursor()
        rf = self.refflat_conn.cursor()
        current_regions = []
        results = self.query_db(pp, "SELECT region_id FROM versions WHERE panel_id=?;", (panel_id,))
        pp.close()
        if len(results) > 0:
            for result in results:
                current_regions.append(result.get('region_id'))
        current_regions = set(current_regions)

        for gene in genes:
            regions = self.query_db(rf,
                               "select distinct regions.id from genes join tx on genes.id=tx.gene_id join exons on tx.id=exons.tx_id join regions on exons.region_id=regions.id where name=? order by start",
                               (gene,))
            for region in regions:
                if region.get('id') not in current_regions:
                    self.add_to_version(panel_id, region.get('id'), version, None, None)

    def import_bed(self,project, panel, gene_file):

        rf = self.refflat_conn.cursor()

        f = open(gene_file, 'r')
        genes = [line.strip('\n') for line in f.readlines()]

        p = Projects()
        project_id = p.get_project(project)
        print project + " id = " + str(project_id)
        if project_id == -1:
            print 'Could not insert project ' + project + "; exiting."
            exit()
        panel_id = self.get_panel_id(panel, project_id)
        print panel + " id = " + str(panel_id)
        if panel_id == -1:
            print 'Could not insert panel ' + panel + "; exiting."
            exit()

        pp = self.panelpal_conn.cursor()
        version = self.query_db(pp, 'SELECT current_version FROM panels WHERE id = ?', (panel_id,))
        pp.close()
        self.insert_versions(genes, panel_id, version[0].get('current_version'))


    def import_pref_transcripts(self, project, transcripts):
        f = open(transcripts, 'r')
        tx_list = [line.strip('\n') for line in f.readlines()]

        pp = self.panelpal_conn.cursor()
        rf = self.refflat_conn.cursor()
        project_id = self.query_db(pp, 'SELECT id fROM projects WHERE name = ?', (project,))[0].get('id')

        for tx in tx_list:
            if tx != tx_list[0]:
                acc = tx.split('\t')[1].split('.')[
                    0]  # splits gene name from transcript and removes version from accession
                try:
                    tx_id = self.query_db(rf, 'SELECT id FROM tx WHERE accession = ?', (acc,))[0].get('id')
                    pp.execute('INSERT INTO pref_tx (project_id, tx_id) VALUES (?,?)', (project_id, tx_id))
                except IndexError:
                    print acc + ' not in refflat database'

    def export_bed(self, panel, bed_type):
        pp = self.panelpal_conn.cursor()

        panel_info = self.query_db(pp, 'SELECT id, current_version FROM panels WHERE name = ?', (panel,))[0]
        panel_id = panel_info.get('id')
        panel_v = panel_info.get('current_version')

        regions = self.query_db(pp,
                              '''SELECT rf.regions.chrom, rf.regions.start, rf.regions.end, rf.exons.number, versions.extension_3, versions.extension_5, rf.genes.name, rf.tx.accession
                                    FROM versions
                                    join regions on rf.regions.id=versions.region_id
                                    join exons on rf.exons.region_id = rf.regions.id
                                    join panels on versions.panel_id=panels.id
                                    join projects on panels.team_id = projects.id
                                    join pref_tx on panels.id=pref_tx.project_id
                                    join rf.tx on rf.tx.id=pref_tx.tx_id
                                    join rf.genes on rf.tx.gene_id = rf.genes.id
                                    WHERE panel_id = ? AND intro <= ? AND (last >= ? OR last ISNULL)''',
                              (panel_id, panel_v, panel_v))

        lines = []
        for region in regions:
            if region.get('extension_3') is None:
                start = region.get('start')
            else:
                start = region.get('start') - region.get('extension_3')

            if region.get('extension_5') is None:
                end = region.get('end')
            else:
                end = region.get('end') + region.get('extension_5')

            line = [region.get('chrom'), start, end, "ex"+str(region.get('number'))+"_"+region.get('name')+"_"+region.get('accession')]
            lines.append("\t".join(str(x) for x in line))
        return "\n".join(lines)


    def get_panel_by_project(project):
        pass

    def check_bed(self, bed_file):
        bed = BedTool(bed_file)
        try:
            sorted_bed = bed.sort()
            merged_bed = sorted_bed.merge(c="4", o="distinct")

            return merged_bed

        except Exception as exception:
            print ("ERROR: " + str(exception))

class Users(Database):
    def query_db(self, c, query, args=(), one=False):
        return Database.query_db(self, c, query, args, one=False)

    def get_users(self):
        pp = self.panelpal_conn.cursor()
        users = self.query_db(pp, "SELECT * FROM users")
        return users

    def add_user(self,user, conn):
        pp = self.panelpal_conn.cursor()
        try:
            pp.execute("INSERT OR IGNORE INTO users(username) VALUES (?)", (user,))
            conn.commit()
            return pp.lastrowid
        except conn.Error as e:
            conn.rollback()
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

#p = Panels()

#p.import_pref_transcripts('NGD', '/results/Analysis/MiSeq/MasterTranscripts/NGD_preferred_transcripts.txt')
#p.import_pref_transcripts('CTD', '/results/Analysis/MiSeq/MasterTranscripts/CTD_preferred_transcripts.txt')
#p.import_pref_transcripts('IEM', '/results/Analysis/MiSeq/MasterTranscripts/IEM_preferred_transcripts.txt')
#p.import_pref_transcripts('Haems', '/results/Analysis/MiSeq/MasterTranscripts/Haems_preferred_transcripts.txt')
#p.import_pref_transcripts('HeredCancer', '/results/Analysis/MiSeq/MasterTranscripts/HeredCancer_preferred_transcripts.txt')
#p.import_bed('NGD', 'HSPRecessive', '/home/bioinfo/Natalie/wc/genes/NGD_HSPrecessive_v1.txt')
#bed = p.export_bed('HSPRecessive')
#print bed
