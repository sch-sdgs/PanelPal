import sqlite3
from pyrefflat import Reader
import argparse


def create_tables(c):
    c.executescript('drop table if exists genes;')
    c.executescript('drop table if exists tx;')
    c.executescript('drop table if exists exons;')
    c.executescript('drop table if exists regions;')

    c.execute('''CREATE TABLE genes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name CHAR(50), UNIQUE(name))''')

    c.execute('''CREATE TABLE tx
        (id INTEGER PRIMARY KEY AUTOINCREMENT, gene_id INTEGER, strand CHAR(1), accession CHAR(30),FOREIGN KEY(gene_id) REFERENCES genes(id), UNIQUE(accession))''')

    c.execute('''CREATE TABLE exons
        (id INTEGER PRIMARY KEY AUTOINCREMENT, tx_id, region_id INTEGER, number INTEGER, FOREIGN KEY(tx_id) REFERENCES tx(id), FOREIGN KEY(region_id) REFERENCES regions(id) )''')

    c.execute('''CREATE TABLE regions
        (id INTEGER PRIMARY KEY AUTOINCREMENT, chrom CHAR(4), start INTEGER, end INTEGER, CONSTRAINT unq UNIQUE (chrom,start,end))''')


def parse_reflat(c,refflat):
    reader = Reader(filename=refflat)
    for record in reader:
        gene = record.gene
        c.execute("INSERT OR IGNORE INTO genes(name) VALUES (?)",(gene,))
        c.execute("SELECT id FROM genes WHERE name=?",(gene,))
        gene_id = c.fetchone()[0]
        tx = record.transcript
        strand = record.strand
        cdsstart = record.cdsStart
        cdsend = record.cdsEnd
        record.tx
        c.execute("INSERT OR IGNORE INTO tx(gene_id,strand,accession) VALUES (?,?,?)", (gene_id, strand, tx))
        c.execute("SELECT id FROM tx WHERE accession=?", (tx,))
        tx_id = c.fetchone()[0]
        for exon in record.exons:
            start = exon._start
            end = exon._end
            chrom = exon._chr
            number = exon._number
            c.execute("INSERT OR IGNORE INTO regions(chrom,start,end) VALUES (?,?,?)",
                      (chrom, start, end))
            c.execute("SELECT id FROM regions WHERE chrom=? AND start=? AND end=?", (chrom,start,end,))
            region_id = c.fetchone()[0]
            c.execute("SELECT id FROM tx WHERE accession=?", (tx,))
            tx_id = c.fetchone()[0]
            c.execute("INSERT OR IGNORE INTO exons(tx_id,region_id,number) VALUES (?,?,?)", (tx_id, region_id, number,))

    c.close()

def main():
    parser = argparse.ArgumentParser(description='creates db of genes, tx and exons for PanelPal')
    parser.add_argument('--refflat',default="/results/Pipeline/reference/UCSCRefSeqTable_refflat_format.txt")
    args = parser.parse_args()

    conn = sqlite3.connect('resources/refflat.db')
    c = conn.cursor()

    create_tables(c)

    parse_reflat(c,args.refflat)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()