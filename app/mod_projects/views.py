from app.queries import *
from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect, flash
from flask.ext.login import login_required, current_user

from app.main import s
from app.views import row2dict,LinkColPrefTx,LinkColConditional
from flask_table import Table, Col, LinkCol
from forms import ProjectForm, EditPermissions
from queries import *

projects = Blueprint('projects', __name__, template_folder='templates')


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
    # username = Col('Username')
    username = Col('User')
    delete = LinkCol('Remove', 'projects.remove_permission',
                     url_kwargs=dict(userid='user_id', projectid='project_id', rel_id='rel_id'))


@projects.route('/')
@login_required
def view_projects(delete=False, project_name=None, project_id=None):
    projects = Projects.query.all()
    result = []
    for i in projects:
        row = row2dict(i)
        row['conditional'] = check_user_has_permission(s, current_user.id, row["id"])
        preftx = get_preftx_by_project_id(s=s, id=row["id"])
        if len(list(preftx)) == 0:
            row['preftx']=False
        else:
            row['preftx']=True
        # if check_user_has_permission(s, current_user.id, row["id"]):
        #     result.append(row)
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
    form = ProjectForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('project_add.html', form=form)
        else:
            create_project(s, name=form.data["name"], user=current_user.id)
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
    print "hello"
    print id
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
        print all_results

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
    preftx_id = request.args.get('id')
    id = get_project_id_by_preftx_id(s,preftx_id)
    if request.method == 'GET':
        result = get_genes_by_projectid_new(s=s, projectid=id)
        genes = {}
        for i in result:
            print i.genename
            preftx_id = get_preftx_by_gene_id(s, id, i.geneid)
            upcoming_preftx = get_upcoming_preftx_by_gene_id(s,id,i.geneid)
            all_tx = get_tx_by_gene_id(s, i.geneid)
            for j in all_tx:
                if preftx_id == j.id:
                    selected = "selected"
                else:
                    selected = ""
                if upcoming_preftx == j.id:
                    genes[i.genename] = list()
                    genes[i.genename].append((0, j.accession + " - This Is a Change Not Made Live Yet", "","red"))
                    break
                else:
                    if i.genename not in genes:
                        genes[i.genename] = list()
                        genes[i.genename].append((j.id, j.accession, selected,""))
                    else:
                        genes[i.genename].append((j.id, j.accession, selected,""))

        list_of_forms = []
        return render_template("preftx_create.html", genes=genes, list_of_forms=list_of_forms, project_id=id,
                               project_name=get_project_name(s, id))

    elif request.method == 'POST':
        print "HERE"
        print request.form
        tx_ids = []
        for i in request.form:
            if i == "project_id":
                project_id = request.form["project_id"]
            else:
                result=dict()
                result["gene"]=i
                result["tx_id"]=request.form[i]
                tx_ids.append(result)
        print tx_ids
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
        return redirect(url_for('edit_permissions', id=project_id))

def check_preftx_status(s, id):
    """
    checks the status of a panel - i.e. whether it is live or not live (it has uncommited changes)

    :param s: db session
    :param id: panel id
    :return: true - panel is live or false - panel has changes
    """
    print "ID" + str(id)
    preftx = check_preftx_status_query(s, id)
    status = True
    for i in preftx:
        print i
        if i.intro > i.current_version:
            status = False
        if i.last is not None:
            if i.last == i.current_version:
                status = False
    return status