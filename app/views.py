from app import app
from models import *
from panel_pal.db_commands import *
import sqlite3
from flask import Flask, render_template, request, flash, url_for, Markup
from forms import UserForm, ProjectForm
from flask_bootstrap import Bootstrap
from flask_table import Table, Col, LinkCol, ButtonCol

app.secret_key = 'development key'

d = Database()
p = Panels()
u = Users()
pro = Projects()

class ItemTable(Table):
    username = Col('Username')
    id = Col('Id')
    delete = LinkCol('Delete', 'delete_record', url_kwargs=dict(id='id', table='table'))

class ItemTableProject(Table):
    name = Col('Name')
    id = Col('Id')
    make = LinkCol('Make Panel','delete_record',url_kwargs=dict())
    delete = LinkCol('Delete','delete_record',url_kwargs=dict(id='id',table='table'))

class ItemTablePanels(Table):
    projectname = Col('Project Name')
    panelname = Col('Panel')
    current_version = Col('Version')
    view = LinkCol('View','panel_detail',url_kwargs=dict(id='panelid'))
    # delete = LinkCol('Delete','delete_record',url_kwargs=dict(id='id',table='table'))
    #

class ItemTablePanel(Table):
    allow_sort = False
    chrom = Col('Chromosome')
    start = Col('Start')
    end = Col('End')
    accession = Col('Accession')
    genename = Col('Gene')
    # delete = LinkCol('Delete','delete_record',url_kwargs=dict(id='id',table='table'))
    #
    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('panel_detail', sort=col_key, direction=direction)

@app.route('/')
def index():
    return render_template('home.html',panels=3)

@app.route('/delete',methods=['GET', 'POST'])
def delete_record():
    conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
    table = request.args.get('table')
    id = request.args.get('id')
    d.delete(conn_panelpal,table,id)
    if table == 'projects':
        return view_projects()
    elif table == 'users':
        return view_users()

@app.route('/panels')
def view_panels():
    panels = p.get_panels()
    table = ItemTablePanels(panels, classes=['table', 'table-striped'])
    return render_template('panels.html',panels=table)

@app.route('/panels/view')
def panel_detail():
    conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
    conn_ref = sqlite3.connect('../panel_pal/resources/refflat.db')
    id = request.args.get('id')
    panel = p.get_panel(conn_panelpal,conn_ref,id)
    genes = []
    for i in panel:
        genes.append(Markup("<a href=\"#\" class=\"btn btn-info btn-md\"><span class=\"glyphicon glyphicon-remove\"></span> "+i["genename"]+"</a>"))
    table = ItemTablePanel(panel, classes=['table', 'table-striped'])
    return render_template('panel_detail.html', panel_detail=table, genes=" ".join(sorted(set(genes))))


@app.route('/users')
def view_users():
    conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
    users = u.get_users(conn_panelpal)
    for i in users:
        id = i["id"]
        i["table"] = "users"
    print users
    table = ItemTable(users,classes=['table', 'table-striped'])
    return render_template('users.html',users=table,)

@app.route('/users/add', methods=['GET', 'POST'])
def add_users():
    form = UserForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('users_add.html', form=form)
        else:
            conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
            id = u.add_user(form.data["name"], conn_panelpal)
            return view_users()

    elif request.method == 'GET':
        return render_template('users_add.html', form=form)


@app.route('/projects')
def view_projects():
    conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
    projects = pro.get_projects(conn_panelpal)
    for i in projects:
        id = i["id"]
        i["table"] = "projects"
    print projects
    table = ItemTableProject(projects,classes=['table', 'table-striped'])
    print table
    return render_template('projects.html',projects=table)

@app.route('/projects/add', methods=['GET', 'POST'])
def add_projects():
    form = ProjectForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('project_add.html', form=form)
        else:
            conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
            id = pro.add_project(form.data["name"], conn_panelpal)
            return view_projects()

    elif request.method == 'GET':
        return render_template('project_add.html', form=form)
