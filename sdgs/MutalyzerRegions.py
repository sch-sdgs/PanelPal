#!/usr/bin/env python

# Example SOAP client for the Mutalyzer web service in Python using the
# suds library.
#
# See https://mutalyzer.nl/webservices
#
# Usage:
#   python client-suds.py 'NM_002001.2:c.1del'
#
# This code is in the public domain; it can be used for whatever purpose
# with absolutely no restrictions.

import sys
from suds.client import Client
import glob, os
import re


def genesforregion(chrom, start, end):
    url = 'https://mutalyzer.nl/services/?wsdl'

    if not chrom.startswith('chr'):
        print 'Chromosome must be in the format chrN'
        sys.exit(1)

    c = Client(url, cache=None)
    o = c.service

    print 'Checking ' + chrom + ':' + start + '-' + end + ' ...'

    r = o.getTranscriptsRange('hg19', chrom, start, end, 1)
    if len(r) < 1:
        print 'No results returned for ' + chrom + ':' + start + '-' + end
        return
    else:
        genes = []
        trans = []
        for transcript in r[0]:
            if transcript.startswith('NM_') and not transcript in trans:
                trans.append(transcript)
                gene = o.getGeneName('hg19', transcript)
                if not gene in genes:
                    genes.append(gene)
        return genes

def genesforbed(bed, outdir):
    outfile = outdir + re.sub("\.bed", ".txt", bed)
    if os.path.isfile(outfile):
        print outfile + ' already exists'
        return

    current = open(bed, 'r')
    content = [line.strip('\n') for line in current.readlines()]

    genes = []
    for region in content:
        if not region.startswith('#'):
            split = region.split('\t')
            g = genesforregion(split[0], split[1], split[2])
            if g is not None:
                for gene in g:
                    if not gene in genes:
                        genes.append(gene)
    print genes

    output = open(outfile, 'w')
    output.write('\n'.join(genes))
    output.close()

def main():
    beddir = sys.argv[1]
    outdir = sys.argv[2]
    os.chdir(beddir)
    for bed in glob.glob("*.bed"):
        print bed
        genesforbed(bed, outdir)





main()