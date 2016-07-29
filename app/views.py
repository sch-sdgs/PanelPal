from app import app
from models import *
from panel_pal.db_commands import *
import sqlite3
from flask import Flask, render_template, request, flash, url_for, Markup
from forms import UserForm, ProjectForm, RemoveGene, AddGene
from flask_bootstrap import Bootstrap
from flask_table import Table, Col, LinkCol, ButtonCol, NumberCol

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

class ItemTablePanel(Table):
    allow_sort = False
    chrom = Col('Chromosome')
    start = NumberCol('Start',valmin=False)
    end = NumberCol('End',valmin=True)
    accession = Col('Accession')
    genename = Col('Gene')
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
    table = request.args.get('table')
    id = request.args.get('id')
    d.delete(table,id)
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
def panel_detail(panel_id=None):
    id = request.args.get('id')
    if id is None:
        id = panel_id
    panel = p.get_panel(id)
    form = RemoveGene()
    add_form = AddGene()
    genes = []
    for i in panel:
        genes.append(Markup("<button class=\"btn btn-info btn-md\" data-id=\""+str(i["panelid"])+"\" data-name=\""+i["genename"]+"\" data-toggle=\"modal\" data-target=\"#removeGene\"><span class=\"glyphicon glyphicon-remove\"></span> "+i["genename"]+"</button>"))
    table = ItemTablePanel(panel, classes=['table', 'table-striped'])
    return render_template('panel_detail.html', panel_name=panel[0]["panelname"],version=panel[0]["current_version"],panel_detail=table, genes=" ".join(sorted(set(genes))),form=form,add_form=add_form,panel_id=id)

@app.route('/panels/delete/gene', methods=['POST'])
def remove_gene():
    form = RemoveGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
        print id
        print gene
        p.remove_gene(id,gene)
    return panel_detail(id)

@app.route('/panels/delete/add', methods=['POST'])
def add_gene():
    form = AddGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
        # print id
        # print gene
        # p.remove_gene(id,gene)
    return panel_detail(id)

@app.route('/users')
def view_users():
    users = u.get_users()
    for i in users:
        id = i["id"]
        i["table"] = "users"
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
            id = u.add_user(form.data["name"])
            return view_users()

    elif request.method == 'GET':
        return render_template('users_add.html', form=form)


@app.route('/projects')
def view_projects():
    projects = pro.get_projects()
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
            id = pro.add_project(form.data["name"])
            return view_projects()

    elif request.method == 'GET':
        return render_template('project_add.html', form=form)
