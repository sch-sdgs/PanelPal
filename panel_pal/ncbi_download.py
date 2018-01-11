import requests
import argparse
import os
import subprocess
import xml.etree.ElementTree as elemtree
import glob
import json
from Bio import SeqIO

def run_splign(in_dir, ncbi, ref_genome):
    try:
        #get files before making genome symlink
        files = os.listdir(in_dir)
        if not os.path.exists(in_dir + 'genome.fa'):
            link_command = 'ln -s ' + ref_genome + ' ' + in_dir + 'genome.fa'
            subprocess.check_call(link_command, shell=True)

        lds_command = ncbi + 'splign -mklds ' + in_dir
        subprocess.check_call(lds_command, shell=True)

        genome_blastdb_command = ncbi + 'makeblastdb -dbtype nucl -parse_seqids -in ' + in_dir + 'genome.fa'
        subprocess.check_call(genome_blastdb_command, shell=True)

        out_file = in_dir + 'cdna.comparts'
        for f in files:
            print(f)
            blastdb_command = ncbi + 'makeblastdb -dbtype nucl -parse_seqids -in ' + in_dir + f
            subprocess.check_call(blastdb_command, shell=True)

            compart_command = ncbi + 'compart -qdb ' + in_dir + f + ' -sdb ' + in_dir + 'genome.fa >> ' + out_file
            subprocess.check_call(compart_command, shell=True)

        splign_command = ncbi + 'splign -min_exon_idty 1 -min_compartment_idty 1 -ldsdir ' + in_dir + ' -comps ' + out_file + ' > ' + in_dir + 'splign.out'
        subprocess.check_call(splign_command, shell=True)

        return in_dir + 'splign.out'
    except subprocess.CalledProcessError as e:
        print('Error executing command: ' + str(e.returncode))
        exit(1)

def get_gene_info(acc, in_dir, retry=False):
    """

    :param acc:
    :param in_dir:
    :param retry:
    :return:
    """
    try:
        acc_id_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nucleotide&term=' + acc + '%5Baccession%5D'
        acc_id_response = requests.get(acc_id_url)

        acc_xml = elemtree.fromstring(acc_id_response.text)
        count = int(acc_xml.find('Count').text)
        if count == 0 and not retry:
            base_acc, version = acc.split('.')
            new_version = int(version) + 1
            new_acc = base_acc + '.' + str(new_version)
            print('No results returned, trying new version ' + new_acc)
            return get_gene_info(new_acc, in_dir, True)
        else:
            acc_id = acc_xml.find('IdList').find('Id').text

        genbank_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&id=" + acc_id + "&rettype=gb"
        genbank_response = requests.get(genbank_url)
        file_name = in_dir + acc + '.gb'
        f = open(file_name, 'w')
        gene_info = dict()
        try:
            f.write(genbank_response.text.encode('utf-8'))
        except UnicodeEncodeError as e:
            print(e)
            print(genbank_response.text)
            exit(1)
        f.close()
        gene_id = 0
        gbs = [rec for rec in SeqIO.parse(file_name, "genbank")]
        # filtered_recs = filter(lambda x: x.id.startswith('NM_'), gbs)
        for rec in gbs:
            cds = [feat for feat in rec.features if feat.type == 'CDS']
            source = [feat for feat in rec.features if feat.type == 'source'][0]
            try:
                gene_info['chrom'] = 'chr' + source.qualifiers['chromosome'][0]
            except KeyError:
                # for elem in xml.iter('SubSource_subtype'):
                #     if elem.attrib['value'] == 'chromosome':
                #         gene_info['chrom'] = 'chr' + elem.text
                pass
            if len(cds) > 1:
                print('WARNING: more than one result for cds feature')
            elif len(cds) == 0:
                gene_info['cds_start'] = -1
                gene_info['cds_end'] = 0
            for feat in cds:
                # if rec.id not in gene_info.keys():
                gene_info['cds_start'] = int(feat.location.start.position)
                gene_info['cds_end'] = int(feat.location.end.position)
            try:
                gene = [feat for feat in rec.features if feat.type == 'gene'][0]
                for i in gene.qualifiers['db_xref']:
                    try:
                        key, value = i.split(':')
                        if key == "GeneID":
                            gene_id = value
                            break
                    except ValueError:
                        pass
                for i in gene.qualifiers['nomenclature']:
                    if 'Official Symbol' in i:
                        items = i.replace(" ", "").split('|')
                        for j in items:
                            try:
                                key, value = j.split(':')
                                if key == "OfficialSymbol":
                                    gene_info['symbol'] = value
                                    break
                            except ValueError:
                                pass
            except KeyError:
                pass
        os.remove(file_name)

        if gene_id == 0:
            gene_search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term=' + acc + '%5BNucleotide%20Accession%5D'
            gene_id_response = requests.get(gene_search_url)
            xml = elemtree.fromstring(gene_id_response.text)
            gene_id = xml.find('IdList').find('Id').text

        gene_summary_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=gene&id=' + str(gene_id) + '&rettype=xml'
        gene_summary_response = requests.get(gene_summary_url)

        xml = elemtree.fromstring(gene_summary_response.text)

        for elem in xml.iter('Gene-commentary'):
            for child in elem.findall('Gene-commentary_heading'):
                if child.text == "GRCh37.p13":
                    for e in elem.iter('Seq-interval'):
                        gene_info['from'] = int(e.find('Seq-interval_from').text)
                        gene_info['to'] = int(e.find('Seq-interval_to').text) + 1
                        gene_info['strand'] = e.find('Seq-interval_strand').find('Na-strand').attrib['value']
                    if 'chrom' not in gene_info.keys():
                        for e in elem.iter('Gene-commentary_label'):
                            if e.text.startswith('Chromosome'):
                                gene_info['chrom'] = 'chr' + e.text.split(' ')[1]
            if 'symbol' not in gene_info.keys():
                for child in elem.findall('Gene-commentary_label'):
                    if child.text == 'Official Symbol':
                        gene_info['symbol'] = elem.find('Gene-commentary_text').text

        return acc, gene_info

    except requests.exceptions.ConnectionError as e:
        print(e)
        print('ERROR: Connection error occurred, this acc will not be in the refflat output')
        print(acc)
        return acc, dict()
    except AttributeError as e:
        print(e)
        print('ERROR: Attribute error occurred, this acc will not be in the refflat output')
        print(acc)
        return acc, dict()
    except KeyError as e:
        print(e)
        print('ERROR: Key error occurred, this acc will not be in the refflat output')
        print(acc)
        return acc, dict()

def check_acc(acc):
    """

    :param acc:
    :return:
    """
    try:
        acc_id_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nucleotide&term=' + acc + '%5Baccession%5D'
        acc_id_response = requests.get(acc_id_url)

        acc_xml = elemtree.fromstring(acc_id_response.text)
        count = int(acc_xml.find('Count').text)

        if count == 0:
            return False
        else:
            return True
    except requests.exceptions.ConnectionError as e:
        print(e)
        print('ERROR: Connection error occurred, this acc will not be in the refflat output')
        print(acc)
        return False
    except AttributeError as e:
        print(e)
        print('ERROR: Attribute error occurred, this acc will not be in the refflat output')
        print(acc)
        return False

def get_fasta(acc, in_dir):
    """

    :param acc:
    :param retry:
    :return:
    """
    acc_id_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nucleotide&term=' + acc + '%5Bacc%5D'
    print(acc_id_url)
    acc_id_response = requests.get(acc_id_url)

    acc_xml = elemtree.fromstring(acc_id_response.text)
    acc_id = acc_xml.find('IdList').find('Id').text

    genbank_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&id=" + acc_id + "&rettype=fasta"
    genbank_response = requests.get(genbank_url)
    file_name = in_dir + 'updated_tx.fa'
    f = open(file_name, 'a')
    try:
        f.write(genbank_response.text.encode('utf-8'))
    except UnicodeEncodeError as e:
        return None, "ERROR" + str(e)
    f.close()


def updated_acc(acc, in_dir):
    """

    :param acc:
    :param in_dir:
    :return:
    """
    checked_acc, gene_info = get_gene_info(acc, in_dir)
    get_fasta(checked_acc, in_dir)

def parse_fasta_files(in_dir, accession_list=dict()):
    """

    :param in_dir:
    :param accession_list:
    :return:
    """
    file_list = glob.glob(in_dir + '*.fna')
    print(file_list)
    if len(file_list) == 0:
        print('ERROR: No files ending .fna were found in the directory provided. Please ensure the NCBI download location is correct and all files are unzipped')
        exit(1)
    else:
        checked_acc_file = open(in_dir + 'checked_acc.txt', 'r')
        checked_acc_list = [x.strip() for x in checked_acc_file.readlines()]
        checked_acc_file.close()

        missing_acc_list = list()
        try:
            missing_acc_file = open(in_dir + 'updated_tx.fa', 'r')
            lines = [x.strip() for x in missing_acc_file.readlines()]
            missing_acc_file.close()
            header_list = filter(lambda l: l.startswith('>'), lines)

            for line in header_list:
                missing_acc_list.append(line.split(' ')[0].split('.')[0].replace('>', ''))
        except IOError:
            pass #if missing_acc file does not exist yet

        for f in file_list:
            print(f)
            f_open = open(f, 'r')
            lines = [x.strip() for x in f_open.readlines()]
            f_open.close()

            ids = filter(lambda l: l.startswith('>'), lines)
            for i in ids:
                fields = i.split(' ')
                acc = fields[0].replace('>', '')
                if acc in accession_list.keys():
                    if acc in checked_acc_list:
                        continue

                    if 'chrom' not in accession_list[acc].keys()or 'symbol' not in accession_list[acc].keys():
                        pass #get gene_info again
                    elif check_acc(acc):
                        checked_acc_list.append(acc)
                        checked_acc_file = open(in_dir + 'checked_acc.txt', 'a')
                        checked_acc_file.write('\n' + acc)
                        checked_acc_file.close()
                        continue
                    else:
                        print('WARNING: accession has been updated since splign run')
                        updated_acc(acc, in_dir)
                        continue
                elif acc.split('.')[0] in missing_acc_list:
                    print(acc + ' already in missing accession file')
                    continue
                elif acc.startswith('NM_') or acc.startswith('NR_'):
                    print(acc)
                    checked_acc, eutils_res = get_gene_info(acc, in_dir)
                    if checked_acc != acc and len(eutils_res.keys()) > 0:
                        print('WARNING: accession has been updated since splign run')
                        updated_acc(acc, in_dir)
                    elif len(eutils_res.keys()) > 0:
                        accession_list[acc] = eutils_res
                        f = open(in_dir + 'accession_list.json', 'w')
                        f.write(json.dumps(accession_list))
                        f.close()
                        checked_acc_list.append(acc)
                        checked_acc_file = open(in_dir + 'checked_acc.txt', 'a')
                        checked_acc_file.write('\n' + acc)
                        checked_acc_file.close()
                elif acc.startswith('X'):
                    continue
                else:
                    print('WARNING: ' + acc + ' doesn\'t match the expected patterns, please check that this should not be included')
        return accession_list

def parse_splign_out(accession_list, splign_out):
    """

    :param accession_list:
    :param splign_out:
    :return:
    """
    f = open(splign_out, 'r')
    lines = [x.strip() for x in f.readlines()]
    f.close()
    splign = dict()

    for line in lines:
        if line.startswith('#'):
            continue
        num, refseq, contig, match_val, length, tx_start, tx_end, g_start, g_end, desc, match = line.split('\t')
        if num.startswith('-'):
            continue
        acc = refseq.split('|')[1]
        if acc.startswith('X'):
            continue
        if match_val == '-' and desc == '<poly-A>':
            continue
        elif match_val == '-':
            print(line)
            print('WARNING: Exon not mapped to genome')
            continue
        exon = {'match':float(match_val), 'tx_start':int(tx_start), 'tx_end':int(tx_end), 'g_start':int(g_start), 'g_end':int(g_end)}
        if acc not in splign.keys():
            splign[acc] = {num:[exon,]}
        elif num not in splign[acc]:
            splign[acc][num] = [exon,]
        else:
            exon_list = splign[acc][num]
            exon_list.append(exon)
            splign[acc][num] = exon_list

    refflat_format = list()
    for acc in accession_list.keys():
        print(acc)
        try:
            splign_result = splign[acc]
            if len(splign_result.keys()) > 1:
                print('WARNING: ' + acc + ' has more than one splign match')
                for result in splign_result.keys():
                    full_match = True
                    min_coord = 1000000000000
                    max_coord = 0
                    strand = '+'
                    for exon in splign_result[result]:
                        if exon['match'] < 1:
                            full_match = False
                            break
                        if exon['g_start'] > exon['g_end']:
                            strand = '-'
                            if exon['g_start'] > max_coord:
                                max_coord = exon['g_start']
                            if exon['g_end'] < min_coord:
                                min_coord = exon['g_end']
                        else:
                            if exon['g_end'] > max_coord:
                                max_coord = exon['g_end']
                            if exon['g_start'] < min_coord:
                                min_coord = exon['g_start']
                    if full_match:
                        if min_coord -1  == accession_list[acc]['from'] and max_coord == accession_list[acc]['to']:
                            print('Found match')
                            print(result)
                            start_list = list()
                            end_list = list()
                            if strand == '+':
                                for exon in splign_result[result]:
                                    start_list.append(exon['g_start'] - 1)
                                    end_list.append(exon['g_end'])
                                    if exon['tx_start'] < accession_list[acc]['cds_start'] < exon['tx_end']:
                                        cds_start = (accession_list[acc]['cds_start'] - exon['tx_start']) + exon[
                                            'g_start']
                                    if exon['tx_start'] < accession_list[acc]['cds_end'] < exon['tx_end']:
                                        cds_end = exon['g_end'] - (exon['tx_end'] - accession_list[acc]['cds_end'])
                            else:
                                for exon in splign_result[result]:
                                    start_list.append(exon['g_end'] - 1)
                                    end_list.append(exon['g_start'])
                                    if exon['tx_start'] < accession_list[acc]['cds_start'] < exon['tx_end']:
                                        cds_end = exon['g_start'] - (
                                        accession_list[acc]['cds_start'] - exon['tx_start']) - 1
                                    if exon['tx_start'] < accession_list[acc]['cds_end'] < exon['tx_end']:
                                        cds_start = (exon['tx_end'] - accession_list[acc]['cds_end']) + exon[
                                            'g_end'] - 1  # half-open coords

                            starts = ','.join(sorted([str(x) for x in start_list])) + ','
                            ends = ','.join(sorted([str(x) for x in end_list])) + ','
                            try:
                                line = [accession_list[acc]['symbol'], acc, accession_list[acc]['chrom'], strand,
                                        accession_list[acc]['from'], accession_list[acc]['to'],
                                        accession_list[acc]['cds_start'], accession_list[acc]['cds_end'],
                                        len(splign_result[result]), starts, ends]
                            except KeyError:
                                print('WARNING: ' + acc + ' does not have a gene symbol assigned')
                                line = ['', acc, accession_list[acc]['chrom'], strand,
                                        accession_list[acc]['from'], accession_list[acc]['to'],
                                        accession_list[acc]['cds_start'], accession_list[acc]['cds_end'],
                                        len(splign_result[result]), starts, ends]
                            refflat_format.append('\t'.join(str(x) for x in line))

                            break
            else:
                print('Only one result')
                start_list = list()
                end_list = list()
                result = splign_result.keys()[0]
                if splign_result[result][0]['g_start'] > splign_result[result][0]['g_end']:
                    strand = '-'
                    for exon in splign_result[result]:
                        start_list.append(exon['g_end'])
                        end_list.append(exon['g_start'])
                        if exon['tx_start'] < accession_list[acc]['cds_start'] < exon['tx_end']:
                            cds_end = exon['g_start'] - (accession_list[acc]['cds_start'] - exon['tx_start']) - 1
                        if exon['tx_start'] < accession_list[acc]['cds_end'] < exon['tx_end']:
                            cds_start = (exon['tx_end'] - accession_list[acc]['cds_end']) + exon['g_end'] - 1 #half-open coords
                else:
                    for exon in splign_result[result]:
                        start_list.append(exon['g_start'])
                        end_list.append(exon['g_end'])
                        if exon['tx_start'] < accession_list[acc]['cds_start'] < exon['tx_end']:
                            cds_start = (accession_list[acc]['cds_start'] - exon['tx_start']) + exon['g_start']
                        if exon['tx_start'] < accession_list[acc]['cds_end'] < exon['tx_end']:
                            cds_end = exon['g_end'] - (exon['tx_end'] - accession_list[acc]['cds_end'])
                    strand = '+'
                starts = ','.join([str(x) for x in sorted(start_list)]) + ','
                ends = ','.join([str(x) for x in sorted(end_list)]) + ','
                try:
                    line = [accession_list[acc]['symbol'], acc, accession_list[acc]['chrom'], strand,
                        accession_list[acc]['from'], accession_list[acc]['to'], cds_start,
                        cds_end, len(splign_result[result]), starts, ends]
                except KeyError:
                    print('WARNING: ' + acc + ' does not have a gene symbol assigned')
                    line = ['', acc, accession_list[acc]['chrom'], strand,
                            accession_list[acc]['from'], accession_list[acc]['to'], cds_start,
                            cds_end, len(splign_result[result]), starts, ends]
                refflat_format.append('\t'.join(str(x) for x in line))
        except KeyError:
            print('ERROR: ' + acc + ' not found in splign output')

    return refflat_format

def main():
    """

    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_dir', help='folder containing the ncbi FTP download for mRNA sequences (N.B. files must be unzipped)')
    parser.add_argument('--ncbi_dir', help='Path to NCBI executables')
    parser.add_argument('--ref', help='Path to reference genome')
    parser.add_argument('--splign_out', help='location of splign output if already run. If None, splign will be run by the script', default=None)

    args = parser.parse_args()

    print('Checking arguments')
    if args.in_dir.endswith('/'):
        in_dir = args.in_dir
    else:
        in_dir = args.in_dir + '/'

    if not os.path.exists(in_dir):
        print('The input directory given does not exist, please check your path and try again')
        exit(1)

    if args.ncbi_dir.endswith('/'):
        ncbi = args.ncbi_dir
    else:
        ncbi = args.ncbi_dir + '/'

    if not os.path.exists(ncbi):
        print('The ncbi directory given does not exist, please check your path and try again')
        exit(1)

    if not os.path.exists(args.ref):
        print('The reference genome location is not correct, please check your path and try again')
        exit(1)

    print('Reading current accession list and checking data...')
    if os.path.exists(in_dir + 'accession_list.json'):
        f = open(in_dir + 'accession_list.json')
        accession_list = json.load(f)
        f.close()
        accession_list = parse_fasta_files(in_dir, accession_list)
    else:
        accession_list = parse_fasta_files(in_dir)

    if not args.splign_out:
        print('Running splign...')
        splign_out = run_splign(in_dir, ncbi, args.ref)
    else:
        print('Splign aready run, output path given as: ' + args.splign_out)
        splign_out = args.splign_out

    print('Parsing splign.out...')
    refflat_format = parse_splign_out(accession_list, splign_out)
    print('Writing out file...')
    f = open(in_dir + 'refflat_format.txt', 'w')
    f.write('\n'.join(refflat_format))
    f.close()
    print('Finished')

if __name__ == "__main__":
    main()
    # gene_info = get_gene_info('NR_002811.1', '/results/Analysis/projects/PanelPal/splign_test/')
    # print(gene_info)