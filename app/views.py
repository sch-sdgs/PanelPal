from flask import render_template, request, flash, url_for, Markup
from flask_table import Table, Col, LinkCol

from app import app, db
from app.queries import *
from forms import UserForm, ProjectForm, RemoveGene, AddGene
from panel_pal.db_commands import *

app.secret_key = 'development key'

d = Database()
p = Panels()
u = Users()
pro = Projects()

s = db.session()

class NumberCol(Col):
    def __init__(self, name ,valmin=False, attr=None, attr_list=None, **kwargs):

        self.valmin = valmin
        super(NumberCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td(self, item, attr):
        return '<td>{}</td>'.format(
            self.td_contents(item, self.get_attr_list(attr)))

    def td_contents(self, item, attr_list):
        if self.valmin:
            valmin = self.from_attr_list(item, attr_list)
            valmax = int(self.from_attr_list(item, attr_list)) + 10000000
            name = "min"
        else:
            valmin = 0
            valmax = self.from_attr_list(item, attr_list)
            name = "max"
        #return '<div class="{name}" data-name="quantity" data-value="{number}" data-valuemin="{valmin}" data-valuemax="{valmax}" data-id="80"></div>'.format(
         #   name=name, number=self.from_attr_list(item, attr_list), valmax=valmax, valmin=valmin)
        id = str(self.from_attr_list(item, ['id'])) + "_" + str(self.from_attr_list(item, attr_list)) + "_" + str(attr_list[0])
        return '<input class="form-control" value="{number}" name="{id}">'.format(number=self.from_attr_list(item, attr_list),id=id)

class ItemTable(Table):
    username = Col('Username')
    id = Col('Id')
    delete = LinkCol('Delete', 'delete_users', url_kwargs=dict(id='id'))


class ItemTableProject(Table):
    name = Col('Name')
    id = Col('Id')
    make = LinkCol('Make Panel', 'delete_record', url_kwargs=dict())
    delete = LinkCol('Delete', 'delete_projects', url_kwargs=dict(id='id'))


class ItemTablePanels(Table):
    projectname = Col('Project Name')
    panelname = Col('Panel')
    current_version = Col('Version')
    view = LinkCol('View', 'panel_detail', url_kwargs=dict(id='panelid'))


class ItemTablePanel(Table):
    allow_sort = False
    chrom = Col('Chromosome')
    start = NumberCol('Start', valmin=False)
    end = NumberCol('End', valmin=True)
    number = Col('Exon')
    accession = Col('Accession')
    genename = Col('Gene')
    delete = LinkCol('Delete', 'delete_projects', url_kwargs=dict(id='id'))

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('panel_detail', sort=col_key, direction=direction)


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d


@app.route('/')
def index():
    return render_template('home.html', panels=3)


@app.route('/delete', methods=['GET', 'POST'])
def delete_record():
    table = request.args.get('table')
    id = request.args.get('id')
    d.delete(table, id)
    if table == 'projects':
        return view_projects()
    elif table == 'users':
        return view_users()


@app.route('/panels')
def view_panels():
    panels = get_panels(db)
    result = []
    for i in panels:
        row = dict(zip(i.keys(), i))
        result.append(row)
    table = ItemTablePanels(result, classes=['table', 'table-striped'])
    return render_template('panels.html', panels=table)


@app.route('/panels/view')
def panel_detail(panel_id=None):
    id = request.args.get('id')
    if id is None:
        id = panel_id
    panel_info = s.query(models.Panels).filter_by(id=id).first()
    version = panel_info.current_version
    panel = get_panel(s,id=id,version=version)

    form = RemoveGene()
    add_form = AddGene()
    result = []
    genes = []
    for i in panel:
        row = dict(zip(i.keys(), i))
        result.append(row)
        genes.append(Markup("<button type=\"button\" class=\"btn btn-info btn-md\" data-id=\"" + str(
            i.panelid) + "\" data-name=\"" + i.genename + "\" data-toggle=\"modal\" data-target=\"#removeGene\"><span class=\"glyphicon glyphicon-remove\"></span> " + i.genename + "</button>"))
    table = ItemTablePanel(result, classes=['table', 'table-striped'])
    return render_template('panel_detail.html', panel_name=result[0]["panelname"], version=result[0]["current_version"],
                           panel_detail=table, genes=" ".join(sorted(set(genes))), form=form, add_form=add_form,
                           panel_id=id)

@app.route('/panels/edit',methods=['POST','GET'])
def edit_panel():
    if request.method == 'POST':
        for v in request.form:
            value = request.form[v]
            id,value,scope = v.split("_")
            s.query(models.Versions).filter_by(id=id).update({models.Versions.extension_5:10})

    s.commit()
    return view_panels()

@app.route('/panels/delete/gene', methods=['POST'])
def remove_gene():
    form = RemoveGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
        panel_info = get_panel(s,id,1)
        ids=[]
        for i in panel_info:
            if i.genename == gene:
                s.query(models.Versions).filter_by(id=i.id).update({models.Versions.last: i.current_version})
                ids.append(i.id)
        new_version = i.current_version + 1
        s.query(models.Panels).filter_by(id=id).update({models.Panels.current_version: new_version})

        # for i in panel:
        #     if i["genename"] == gene:
        #         id = i["id"]
        #         intro = i["intro"]
        #         current_version = i["current_version"]
        #         print id
        #         pp.execute('UPDATE versions SET last = ? WHERE id = ?', (current_version, id,))
        #         ids.append(id)
        # new_version = current_version + 1
        # pp.execute('UPDATE panels SET current_version = ? WHERE id = ?', (new_version, panel_id,))
        # self.panelpal_conn.commit()


        # p.remove_gene(id, gene)
    return panel_detail(id)


@app.route('/panels/delete/add', methods=['POST'])
def add_gene():
    form = AddGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
    return panel_detail(id)


@app.route('/users')
def view_users():
    users = models.Users.query.all()
    result = []
    for i in users:
        row = row2dict(i)
        result.append(row)
    table = ItemTable(result, classes=['table', 'table-striped'])
    return render_template('users.html', users=table, )


@app.route('/users/add', methods=['GET', 'POST'])
def add_users():
    form = UserForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('users_add.html', form=form)
        else:
            u = models.Users(username=form.data["name"])
            db.session.add(u)
            db.session.commit()
            return view_users()

    elif request.method == 'GET':
        return render_template('users_add.html', form=form)


@app.route('/users/delete', methods=['GET', 'POST'])
def delete_users():
    u = db.session.query(models.Users).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_users()


@app.route('/projects')
def view_projects():
    projects = models.Projects.query.all()
    result = []
    for i in projects:
        print type(i)
        row = row2dict(i)
        result.append(row)
    table = ItemTableProject(projects, classes=['table', 'table-striped'])
    return render_template('projects.html', projects=table)


@app.route('/projects/add', methods=['GET', 'POST'])
def add_projects():
    form = ProjectForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('project_add.html', form=form)
        else:
            u = models.Projects(name=form.data["name"])
            db.session.add(u)
            db.session.commit()
            return view_projects()

    elif request.method == 'GET':
        return render_template('project_add.html', form=form)


@app.route('/projects/delete', methods=['GET', 'POST'])
def delete_projects():
    u = db.session.query(models.Projects).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_projects()
