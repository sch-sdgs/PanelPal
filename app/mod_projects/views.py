from collections import OrderedDict

from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect, flash
from flask_login import login_required, current_user
from flask_table import Table, Col, LinkCol

from app.panel_pal import s
from app.views import LinkColConditional
from forms import ProjectForm, EditPermissions
from queries import *

projects = Blueprint('projects', __name__, template_folder='templates')


class LinkColPrefTx(LinkCol):
    def td_contents(self, item, attr_list):
        if item["preftx"] is True:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'

class ItemTableProject(Table):
    name = Col('Name')
    view = LinkCol('View Panels', 'panels.view_panels', url_kwargs=dict(id='id'))
    pref_tx = LinkColPrefTx('View Preferred Tx', 'projects.view_preftx', url_kwargs=dict(id='id'))
    permissions = LinkColConditional('Edit Permissions', 'projects.edit_permissions', url_kwargs=dict(id='id'))
    # make = LinkCol('Make Panel', '', url_kwargs=dict())
    delete = LinkColConditional('Delete', 'projects.delete_project', url_kwargs=dict(id='id'))

class ItemTablePrefTx(Table):
    genename = Col('Gene Name')
    accession = Col('Accession')
    tx_start = Col('Transcript Start')
    tx_end = Col('Transcript End')
    strand = Col('Strand')


class ItemTablePermissions(Table):
    username = Col('User')
    delete = LinkCol('Remove', 'projects.remove_permission',
                     url_kwargs=dict(userid='user_id', projectid='project_id', rel_id='rel_id'))

def row2dict(row):
    """
    converts a database row from certain queries (I think .all() style queries) to a dict
    :param row: row from db
    :return: dict
    """
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d

@projects.route('/')
@login_required
def view_projects(delete=False, project_name=None, project_id=None):
    projects = Projects.query.all()
    result = []
    for i in projects:
        row = row2dict(i)
        row['permission'] = check_user_has_permission(s, current_user.id, row["id"])
        preftx = get_preftx_by_project_id(s=s, id=row["id"])
        print "PREFTX"
        print "----"
        if len(list(preftx)) == 0:
            row['preftx']=False
        else:
            print "HELLO"
            row['preftx']=True
        result.append(row)
    table = ItemTableProject(result, classes=['table', 'table-striped'])
    return render_template('projects.html', projects=table, delete=delete, project_name=project_name,
                           project_id=project_id)


@projects.route('/experimental')
@login_required
def project_tree():
    id = request.args.get('id')
    all = get_all_by_project_id(s, id)
    projects = dict()
    for i in all:
        if i.projectname not in projects:
            projects[i.projectname] = dict()
        if i.panelname not in projects[i.projectname]:
            projects[i.projectname][i.panelname] = list()
        projects[i.projectname][i.panelname].append(i.vpname)

    return render_template('project_view.html', projects=projects)


@projects.route('/projects/add', methods=['GET', 'POST'])
@login_required
def add_projects():
    form = ProjectForm(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('project_add.html', form=form)
        else:
            choice = filter(lambda c: c[0] == form.name.data, form.name.choices)[0]
            print(choice)
            project_abv = choice[0]
            project_name = choice[1]
            id = create_project(s, name=project_name, short_name=project_abv, user=current_user.id)
            if id == -1:
                form.name.errors = ["That name isn't unique.",]
                return render_template('project_add.html', form=form)
            return view_projects()

    elif request.method == 'GET':
        return render_template('project_add.html', form=form)


@projects.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_project():
    # todo display a modal here with "do you really want to delete?" message
    id = request.args.get('id')
    if request.args.get('check'):
        u = s.query(Projects).filter_by(id=id).first()
        s.delete(u)
        s.commit()
        return view_projects()
    else:
        return view_projects(delete=True, project_name="Test", project_id=id)


@projects.route('/preftx')
@login_required
def view_preftx():
    id = request.args.get('id')
    project = get_project_name(s, id)
    result = get_preftx_by_project_id(s=s, id=id)
    if len(list(result)) == 0:
        return redirect(url_for('create_preftx', id=id))
    else:
        result = get_preftx_by_project_id(s=s, id=id)
        all_results = []
        for i in result:
            preftx_id = i.preftx_id
            row = dict(zip(i.keys(), i))
            all_results.append(row)

        if check_user_has_permission(s, current_user.id, id):
            edit = ''
        else:
            edit = 'disabled'

        table = ItemTablePrefTx(all_results, classes=['table', 'table-striped'])
        status = check_preftx_status(s,preftx_id)
        version = get_current_preftx_version(s,preftx_id)
    return render_template("preftx.html", preftx=table, project_name=project, preftxid=preftx_id, version=version, edit=edit, status=status)


@projects.route('/preftx/create', methods=['GET', 'POST'])
@login_required
def create_preftx():
    print  request.args.get('id')
    preftx_id_master = request.args.get('id')
    project_id = get_project_id_by_preftx_id(s,preftx_id_master)
    if request.method == 'GET':
        result = get_genes_by_projectid_new(s=s, projectid=project_id)
        genes = OrderedDict()
        for i in result:
            preftx_id = get_preftx_by_gene_id(s, project_id, i.geneid)
            upcoming_preftx = get_upcoming_preftx_by_gene_id(s,preftx_id_master,i.geneid)
            all_tx = get_tx_by_gene_id(s, i.geneid)
            genes[i.genename] = {"upcoming": False, "tx": list()}
            for j in all_tx:
                print(j)

                if upcoming_preftx == j.id:
                    selected = "selected"
                elif preftx_id == j.id:
                    selected = "current"
                else:
                    selected = ""

                if upcoming_preftx == j.id:
                    genes[i.genename]["upcoming"] = True
                    genes[i.genename]["tx"].append((j.id, j.accession + " - This Is a Change Not Made Live Yet", selected,"red"))
                else:
                    if i.genename not in genes:
                        genes[i.genename]["tx"].append((j.id, j.accession, selected,""))
                    else:
                        genes[i.genename]["tx"].append((j.id, j.accession, selected,""))

        print genes

        return render_template("preftx_create.html", genes=genes, project_id=project_id,
                               project_name=get_project_name(s, project_id))

    elif request.method == 'POST':
        print "HERE"
        print project_id
        print request.form
        tx_ids = []
        for i in request.form:
            if i == "project_id":
                project_id = request.form["project_id"]
            else:
                result=dict()
                result["gene"]=i
                result["tx_id"]=request.form[i].replace(' - This Is a Change Not Made Live Yet', '')
                tx_ids.append(result)
        print tx_ids
        print project_id
        add_preftxs_to_panel(s, project_id, tx_ids)
        return redirect(url_for('projects.view_preftx', id=project_id))

@projects.route('/preftx/live')
def make_tx_live():
    id = request.args.get('pref_tx')
    current_version = get_current_preftx_version(s, id)
    new_version = current_version + 1
    make_preftx_live(s, id, new_version, current_user.id)
    project_id = get_project_id_by_preftx_id(s,id)
    return redirect(url_for('projects.view_preftx',id=project_id))


@projects.route('/preftx/add_pref_tx', methods=['POST'])
@login_required
def add_pref_tx():
    """

    :return:
    """
    gene_id = request.args.get('gene_id')
    tx = get_tx_by_gene_id(s, gene_id)
    return jsonify(tx)


@projects.route("/edit_permissions", methods=['GET', 'POST'])
@login_required
def edit_permissions():
    id = request.args.get('id')
    form = EditPermissions(project_id=id)
    message = None
    if request.method == 'POST':
        if check_user_has_permission(s, current_user.id, form.data["project_id"]):
            add_user_project_rel(s, form.data["user_id"].id, form.data["project_id"])
        else:
            message = "You do not have permission to edit this project"
        id = form.data["project_id"]
    result = get_user_rel_by_project_id(s, project_id=id)
    all_results = []
    for i in result:
        row = dict(zip(i.keys(), i))
        all_results.append(row)

    project = get_project_name(s, id)
    table = ItemTablePermissions(all_results, classes=['table', 'table-striped'])
    return render_template("permissions.html", table=table, form=form, project_name=project, message=message)

@projects.route("/remove_permissions")
@login_required
def remove_permission():
    panel_id = request.args.get('panelid')
    project_id = request.args.get('projectid')
    rel_id = request.args.get('rel_id')
    if check_user_has_permission(s, current_user.id, project_id):
        remove_user_project_rel(s, rel_id)
        return redirect(url_for('projects.edit_permissions', id=project_id))

def check_preftx_status(s, id):
    """
    checks the status of a panel - i.e. whether it is live or not live (it has uncommited changes)

    :param s: db session
    :param id: panel id
    :return: true - panel is live or false - panel has changes
    """
    preftx = check_preftx_status_query(s, id)
    status = True
    for i in preftx:
        if i.intro > i.current_version:
            status = False
        if i.last is not None:
            if i.last == i.current_version:
                status = False
    return status