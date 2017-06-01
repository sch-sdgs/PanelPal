import os
import sqlite3
from pybedtools import BedTool
import subprocess

def main():
    bed = "http://10.182.131.21/results/Analysis/MiSeq/MasterBED/Bleeding_Panel_v1.bed"
    panel = "BMF"

    command = 'export PATH=${PATH}:/results/Pipeline/program/bedtools-2.17.0/bin'
    print(command)
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(command)
        print('Error executing command: ' + str(e.returncode))
        exit(1)

    path = os.path.dirname(os.path.dirname(__file__))
    panelpal = path + '/resources/panel_pal.db'
    panelpal_conn = sqlite3.connect(panelpal, check_same_thread=False)
    c = panelpal_conn.cursor()

    results = c.execute("SELECT id FROM panels WHERE panels.name = ?", (panel,))
    for i in results:
        print(i[0])
        panel_id = i[0]

    sql = """CREATE TEMP TABLE _custom AS SELECT regions.chrom,
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start - 25 ELSE regions.start - versions.extension_5 - 25 END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" + 25 ELSE regions."end" + versions.extension_3 + 25 END AS region_end,
                    regions.name AS name
                    FROM panels
                    JOIN versions ON versions.panel_id = panels.id
                    JOIN regions ON regions.id = versions.region_id
                    WHERE panels.id = ? AND versions.intro <= ? AND (versions.last >= ? OR versions.last IS NULL) AND regions.name IS NOT NULL"""
    c.execute(sql, (panel_id, 1, 1))

    sql = """SELECT regions.chrom,
                    CASE WHEN (versions.extension_5 IS NULL) THEN regions.start - 25 ELSE regions.start - versions.extension_5 - 25 END AS region_start,
                    CASE WHEN (versions.extension_3 IS NULL) THEN regions."end" + 25 ELSE regions."end" + versions.extension_3 + 25 END AS region_end,
                    group_concat(DISTINCT tx.accession || "_" || genes.name|| "_exon" || CAST(exons.number AS VARCHAR)) AS name
                    FROM panels
                    JOIN versions ON versions.panel_id = panels.id
                    JOIN regions ON regions.id = versions.region_id
                    JOIN exons ON regions.id = exons.region_id
                    JOIN tx ON tx.id = exons.tx_id
                    JOIN genes ON genes.id = tx.gene_id
                    WHERE panels.id = ? AND versions.intro <= ? AND (versions.last >= ? OR versions.last IS NULL)
                    GROUP BY regions.id
                    UNION SELECT * FROM _custom
                    ORDER BY chrom,region_start;"""
    results = c.execute(sql, (panel_id, 1, 1))

    regions = []
    for r in results:
        print(r)
        line = "\t".join(str(x) for x in [r[0], r[1], r[2], r[3]])
        regions.append(line)

    bed_string = '\n'.join(regions)
    f = open("/home/bioinfo/Natalie/bed_comp/Haems_BMF_exported.bed", 'w')
    f.write(bed_string)
    f.close()
    # exported_bed = BedTool(bed_string, from_string=True)
    #
    # original_bed = BedTool(bed)
    #
    # missing_from_exported = original_bed.subtract(exported_bed)
    # missing_from_original = exported_bed.subtract(original_bed)
    #
    # missing_from_exported.saveas("/home/bioinfo/Natalie/bed_comp/CTD_missing_from_exported.txt")
    # missing_from_original.saveas("/home/bioinfo/Natalie/bed_comp/CTD_missing_from_original.txt")



if __name__ == "__main__":
    main()