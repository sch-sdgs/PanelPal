from collections import OrderedDict

from app.mod_admin.queries import *
from app.mod_panels.queries import  unlock_panel_query
from queries import check_if_admin, get_user_id_by_username, check_tx
from flask import Blueprint
from flask import render_template, request, url_for, redirect
from flask_login import login_required, login_user, logout_user, current_user, UserMixin
from functools import wraps

from app.panel_pal import s, app
from app.activedirectory import UserAuthentication
from app.mod_projects.queries import get_all_projects, get_projects_by_user, remove_user_project_rel_no_id, add_user_project_rel
from flask_table import Table, Col, LinkCol
from forms import UserForm, NewTxForm
from queries import create_user, toggle_admin_query

import requests
import xml.etree.ElementTree as elemtree
import os
import subprocess
from Bio import SeqIO

class ItemTableUsers(Table):
    username = Col('User')
    admin = Col('Admin')
    toggle_admin = LinkCol('Toggle Admin', 'admin.toggle_admin', url_kwargs=dict(id='id'))


class ItemTableLocked(Table):
    name = Col('Panel')
    username = Col('Locked By')
    toggle_lock = LinkCol('Toggle Lock', 'admin.toggle_locked', url_kwargs=dict(id='id'))

class User(UserMixin):
    """
    Defines methods for users for authentication. Each user has an id (username) and a password

    """
    def __init__(self, id, password=None):
        self.id = id
        self.password = password

    def is_authenticated(self, s, id, password):
        """
        Method to check if user is authenticated. The method checks the database for the username and then active
        directory for username and password authentication

        :param s: SQLAlechmy session token
        :param id: ID of the user (username)
        :param password: password the user has entered into the application
        :return: True if the user authenticates, false if not
        """
        validuser = get_user_by_username(s, id)
        if len(list(validuser)) == 0:
            return False
        else:
            check_activdir = UserAuthentication().authenticate(id, password)

            if check_activdir != "False":
                return True
            else:
                return False

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

admin = Blueprint('admin', __name__, template_folder='templates')

def admin_required(f):
    """
    This method allows others to require the user to have admin permissions to execute

    :param f:
    :return:
    """
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if check_if_admin(s,current_user.id) is False:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/user', methods=['GET', 'POST'])
@login_required
@admin_required
def user_admin():
    """
    view to allow users to be added and admin rights toggled

    :return: render html template
    """
    form = UserForm()
    message = None
    if request.method == 'POST':
        username = request.form["name"]
        if check_if_admin(s, current_user.id):
            create_user(s, username)
            message = "Added user: " + username
        else:
            return render_template('users.html', form=form, message="You can't do that")
    users = get_users(s)
    result = []
    for i in users:
        if i.username != current_user.id:
            row = dict(zip(i.keys(), i))
            result.append(row)
    table = ItemTableUsers(result, classes=['table', 'table-striped'])
    return render_template('users.html', form=form, table=table, message=message)


@admin.route('/user/toggle', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_admin():
    """
    toggles admin rights of a user

    :return: redirect to user_admin
    """
    user_id = request.args.get('id')
    toggle_admin_query(s, user_id)
    return redirect(url_for('admin.user_admin'))


@admin.route('/locked/toggle', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_locked():
    """
    toggles the locked status of a panel

    useful if someone has forgotten they have left a panel locked - an admin can unlock

    :return: view_locked method
    """
    panel_id = request.args.get('id')
    unlock_panel_query(s, panel_id)
    return view_locked(message="Panel Unlocked")


@admin.route('/logs', methods=['GET', 'POST'])
@login_required
@admin_required
def view_logs():
    """
    view admin logs so that you can see what users have been doing

    :return: render html template
    """
    if request.args.get('file'):
        log = request.args.get('file')
    else:
        log = '/tmp/PanelPal.log'

    import glob
    files = []
    listing = glob.glob('/tmp/PanelPal*log*')
    for filename in listing:
        files.append(filename)

    result = []
    with open(log) as f:
        for line in f:
            result.append(line.rstrip())

    return render_template('logs.html', log=result, files=files)


@admin.route('/locked', methods=['GET', 'POST'])
@login_required
@admin_required
def view_locked(message=None):
    """
    view locked panels

    :param message: message to display
    :return: rendered html template
    """
    locked = get_all_locked(s)
    result = []
    for i in locked:
        row = dict(zip(i.keys(), i))
        result.append(row)
    table = ItemTableLocked(result, classes=['table', 'table-striped'])
    return render_template('locked.html', table=table, message=message)


@admin.route("/permissions", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_permissions_admin():
    """
    edit permissions of users to allow editing of panels belonging to projects

    :return: rendered html template
    """
    users = get_users(s)
    result = OrderedDict()
    message = None
    for i in users:
        username = get_username_by_user_id(s, i.id)
        result[username] = dict()
        user_projects = get_projects_by_user(s, username)
        all_projects = get_all_projects(s)
        for p in all_projects:
            result[username][p.id] = {'name': p.name, 'checked': ''}
        for u in user_projects:
            result[username][u.id] = {'name': u.name, 'checked': 'checked'}

    if request.method == 'POST':
        status = {}
        for i in request.form.getlist('check'):
            print i
            username, project_id = i.split("_")
            print username
            print status
            if username not in status:
                status[username] = list()
                status[username].append(int(project_id))
            else:
                status[username].append(int(project_id))
        message = "Your changes have been made"

        print status
        # find changes
        for username in result:
            print username
            for project_id in result[username]:
                checked = result[username][project_id]["checked"]
                name = result[username][project_id]["name"]
                if username in status:
                    if checked == "checked":
                        print status[username]
                        print project_id
                        if project_id in status[username]:
                            # this is OK it's checked and project
                            pass
                        else:
                            # not OK - it's been unchecked
                            print "username in but UNCHECKED"
                            remove_user_project_rel_no_id(s, username, project_id)
                    else:
                        if project_id in status[username]:
                            user_id = get_user_id_by_username(s, username)
                            add_user_project_rel(s, user_id, project_id)
                            print "NOW CHECKED"
                else:
                    if checked == "checked":
                        print "UNCHECKED"
                        remove_user_project_rel_no_id(s, username, project_id)

    users = get_users(s)
    result = OrderedDict()
    for i in users:
        username = get_username_by_user_id(s, i.id)
        result[username] = dict()
        user_projects = get_projects_by_user(s, username)
        all_projects = get_all_projects(s)
        for p in all_projects:
            row = dict(zip(p.keys(), p))
            result[username][p.id] = {'name': p.name, 'checked': ''}
        for u in user_projects:
            result[username][u.id] = {'name': u.name, 'checked': 'checked'}

    return render_template("permissions_admin.html", permissions=result, message=message)

@admin.route("/FAQ", methods=["GET", "POST"])
def faq_page():
    """
    Displays the FAQs for PanelPal

    :return: render FAQ template
    """
    return render_template("faq.html")

def get_fasta(acc, retry=False):
    """

    :param acc:
    :param retry:
    :return:
    """
    acc_id_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nucleotide&term=' + acc + '%5Baccession%5D'
    print(acc_id_url)
    acc_id_response = requests.get(acc_id_url)

    acc_xml = elemtree.fromstring(acc_id_response.text)
    count = int(acc_xml.find('Count').text)
    if count == 0 and not retry:
        base_acc, version = acc.split('.')
        new_version = int(version) + 1
        new_acc = base_acc + '.' + str(new_version)
        print('No results returned, trying new version ' + new_acc)
        return get_fasta(new_acc, True)
    else:
        acc_id = acc_xml.find('IdList').find('Id').text

    genbank_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&id=" + acc_id + "&rettype=fasta"
    genbank_response = requests.get(genbank_url)
    basedir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_name = basedir + '/resources/' + acc + '.fa'
    f = open(file_name, 'w')
    try:
        f.write(genbank_response.text.encode('utf-8'))
    except UnicodeEncodeError as e:
        return None, "ERROR" + str(e)
    f.close()
    return acc, acc_id, file_name

def run_splign(fasta_file):
    """

    :param fasta_file:
    :return:
    """
    try:
        #get files before making genome symlink
        resources = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/resources/'
        if not os.path.exists(resources + 'genome.fa'):
            return "ERROR: reference genome file not found."

        lds_command = resources + 'splign -mklds ' + resources
        subprocess.check_call(lds_command, shell=True)

        genome_blastdb_command = resources + 'makeblastdb -dbtype nucl -parse_seqids -in ' + resources + 'genome.fa'
        subprocess.check_call(genome_blastdb_command, shell=True)

        out_file = resources + 'cdna.comparts'
        blastdb_command = resources + 'makeblastdb -dbtype nucl -parse_seqids -in ' + fasta_file
        subprocess.check_call(blastdb_command, shell=True)

        compart_command = resources + 'compart -qdb ' + fasta_file + ' -sdb ' + resources + 'genome.fa >> ' + out_file
        subprocess.check_call(compart_command, shell=True)

        splign_command = resources + 'splign -min_exon_idty 1 -min_compartment_idty 1 -ldsdir ' + resources + ' -comps ' + out_file + ' > ' + resources + 'splign.out'
        print(splign_command)
        subprocess.check_call(splign_command, shell=True)

        os.remove(fasta_file)

        return resources + 'splign.out'
    except subprocess.CalledProcessError as e:
        print('Error executing command: ' + str(e.returncode))
        return "ERROR:" + str(e)

def get_gene_info(acc_id, acc):
    """

    :param acc_id:
    :param acc:
    :return:
    """
    try:
        resources = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/resources/'

        genbank_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nucleotide&id=" + acc_id + "&rettype=gb"
        genbank_response = requests.get(genbank_url)
        file_name = resources + acc + '.gb'
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

        gene_summary_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=gene&id=' + str(
            gene_id) + '&rettype=xml'
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

        return gene_info

    except requests.exceptions.ConnectionError as e:
        print(e)
        print('ERROR: Connection error occurred, this acc will not be in the refflat output')
        print(acc)
        return {"ERROR": 'ERROR: Connection error occurred, this acc will not be in the refflat output'}
    except AttributeError as e:
        print(e)
        print('ERROR: Attribute error occurred, this acc will not be in the refflat output')
        print(acc)
        return {"ERROR":'ERROR: Attribute error occurred, this acc will not be in the refflat output'}
    except KeyError as e:
        print(e)
        print('ERROR: Key error occurred, this acc will not be in the refflat output')
        print(acc)
        return {"ERROR":'ERROR: Key error occurred, this acc will not be in the refflat output'}

@admin.route("/new-tx", methods=['GET', 'POST'])
def add_new_tx():
    """
    View to add a new tx to the database using NCBI eutils and splign

    Method checks tx name is not in database - currently does not handle new versions (issue #79).
    If the tx does not exist in the db the method will download the fasta file, run splign and add the new
    co-ordinates to the database.

    :return:
    """
    if request.method == 'POST':
        form = NewTxForm(request.form)
        if len(form.accession.errors) == 0:
            acc = form.accession.data
            count = check_tx(s, acc)
            if count > 0:
                return render_template('add_tx.html', form=form, message=render_template('tx_already_exists.html', acc=acc))
            else:
                checked_acc, acc_id, fasta_file = get_fasta(acc)
                if acc != checked_acc:
                    error_message = "The version given was not found in NCBI, the current accession version is " + checked_acc
                    return render_template('add_tx.html', form=form,
                                           message=render_template('tx_upload_error.html', acc=acc, error=error_message))
                if not acc_id:
                    return render_template('add_tx.html', form=form,
                                    message=render_template('tx_upload_error.html', acc=acc, error=fasta_file))

                splign = run_splign(fasta_file)
                if splign.startswith('ERROR'):
                    return render_template('add_tx.html', form=form,
                                    message=render_template('tx_upload_error.html', acc=acc, error=splign))

                gene_info = get_gene_info(acc_id, acc)
                if "ERROR" in gene_info.keys():
                    return render_template('add_tx.html', form=form,
                                           message=render_template('tx_upload_error.html', acc=acc, error=gene_info["ERROR"]))




        else:#form doesn't validate
            return render_template('add_tx.html', form=form)
    else:
        form = NewTxForm()
        return render_template('add_tx.html', form=form)