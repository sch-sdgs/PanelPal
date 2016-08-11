from flask import render_template, request, flash, url_for, Markup, jsonify
from flask_table import Table, Col, LinkCol

from app import app, db, s,models
from app.queries import *
from forms import UserForm, ProjectForm, RemoveGene, AddGene, CreatePanel
from panel_pal.db_commands import *
from sqlalchemy.orm import scoped_session
from sqlalchemy import Table as TableSQL
from flask import session

app.secret_key = 'development key'

d = Database()
p = Panels()
u = Users()
pro = Projects()


class NumberCol(Col):
    def __init__(self, name, valmin=False, attr=None, attr_list=None, **kwargs):
        self.valmin = valmin
        super(NumberCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        id = "region_" + str(self.from_attr_list(item, ['region_id'])) + "_" + str(
            self.from_attr_list(item, ['intro'])) + "_" + str(
            self.from_attr_list(item, ['last'])) + "_" + str(
            self.from_attr_list(item, ['current_version'])) + "_" + str(self.from_attr_list(item, ['id'])) + "_" + str(
            self.from_attr_list(item, ['original_start'])) + "_" + str(
            self.from_attr_list(item, ['extension_5'])) + "_" + str(
            self.from_attr_list(item, ['original_end'])) + "_" + str(
            self.from_attr_list(item, ['extension_3'])) + "_" + str(attr_list[0])
        # todo add an id to teh input class so you can check if starts are less than ends?
        return '<input class="form-control" value="{number}" name="{id}">'.format(
            number=self.from_attr_list(item, attr_list), id=id)


class LabelCol(Col):
    def __init__(self, name, valmin=False, attr=None, attr_list=None, **kwargs):

        self.valmin = valmin
        super(LabelCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        if self.from_attr_list(item, attr_list):
            type = "success"
            status = "OK"
        else:
            type = "danger"
            status = "Changes"

        return '<p><span class="label label-{type}">{status}</span></p>'.format(type=type, status=status)


class ItemTable(Table):
    username = Col('Username')
    id = Col('Id')
    delete = LinkCol('Delete', 'delete_users', url_kwargs=dict(id='id'))


class ItemTableProject(Table):
    name = Col('Name')
    id = Col('Id')
    view = LinkCol('View Panels', 'view_panels', url_kwargs=dict(id='id'))
    #make = LinkCol('Make Panel', '', url_kwargs=dict())
    delete = LinkCol('Delete', 'delete_project', url_kwargs=dict(id='id'))


class ItemTablePanels(Table):
    projectname = Col('Project Name')
    panelname = Col('Panel')
    current_version = Col('Stable Version')
    status = LabelCol('Status')
    make_live = LinkCol('Make Live', 'make_live', url_kwargs=dict(id='panelid'))
    edit = LinkCol('Edit', 'edit_panel_page', url_kwargs=dict(id='panelid'))


class ItemTablePanel(Table):
    allow_sort = False
    status = LabelCol('')
    chrom = Col('Chromosome')
    start = NumberCol('Start', valmin=False)
    end = NumberCol('End', valmin=True)
    number = Col('Exon')
    accession = Col('Accession')
    genename = Col('Gene')
    delete = LinkCol('Delete', 'delete_region', url_kwargs=dict(id='id'))

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('edit_panel_page', sort=col_key, direction=direction)


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d


@app.route('/')
def index():
    return render_template('home.html', panels=3)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    value = str(request.args.get('q'))
    result = s.query(models.Genes).filter(models.Genes.name.like("%"+value+"%")).all()
    data = [i.name for i in result]
    print data
    return jsonify(matching_results=data)


########################
# PANELS
########################

@app.route('/panels', methods=['GET', 'POST'])
def view_panels(id=None):
    if not id:
        id = request.args.get('id')
    if id:
        panels = get_panels_by_project_id(s, id)
    else:
        panels = get_panels(s)
    result = []
    project_name = 'All'
    for i in panels:
        row = dict(zip(i.keys(), i))
        status = check_panel_status(s, row["panelid"])
        row["status"] = status
        if id:
            project_name = row['projectname']
        result.append(row)
    table = ItemTablePanels(result, classes=['table', 'table-striped'])
    return render_template('panels.html', panels=table, project_name=project_name)


@app.route('/panels/create', methods=['GET', 'POST'])
def create_panel():
    form = CreatePanel()
    if request.method == 'POST':
        # if form.validate() == False:
        #     flash('All fields are required.')
        #     return render_template('panel_create.html', form=form)
        # else:
        print request.form

        return edit_panel_page(panel_id=1)

    elif request.method == 'GET':
        return render_template('panel_create.html', form=form)




@app.route('/panels/live', methods=['GET', 'POST'])
def make_live():
    id = request.args.get('id')
    panel = s.query(models.Panels).filter_by(id=id).first()
    new_version = panel.current_version + 1
    s.query(models.Panels).filter_by(id=id).update({models.Panels.current_version: new_version})
    project = s.query(models.Panels, models.Projects).filter_by(id=id).join(models.Projects).values(
        models.Projects.id.label("projectid"))
    for i in project:
        projectid = i.projectid
    s.commit()
    return view_panels(id=projectid)


@app.route('/panels/edit')
def edit_panel_page(panel_id=None):
    id = request.args.get('id')
    if id is None:
        id = panel_id
    panel_info = s.query(models.Panels).filter_by(id=id).first()
    version = panel_info.current_version
    name = panel_info.name
    panel = get_panel_edit(s, id=id, version=version)

    form = RemoveGene()
    add_form = AddGene()
    result = []
    genes = []
    for i in panel:
        row = dict(zip(i.keys(), i))
        row['original_start'] = row["start"]
        row['original_end'] = row["end"]
        if row["intro"] > row["current_version"]:
            row["status"] = False
        else:
            row["status"] = True
        result.append(row)
        if row["extension_5"]:
            row["start"] = int(row["start"]) + int(row["extension_5"])
        if row["extension_3"]:
            row["end"] = int(row["end"]) + int(row["extension_3"])
        genes.append(Markup("<button type=\"button\" class=\"btn btn-danger btn-md btngene\" data-id=\"" + str(
            i.panelid) + "\" data-name=\"" + i.genename + "\" data-toggle=\"modal\" data-target=\"#removeGene\" id=\"myDeleteButton\"><span class=\"glyphicon glyphicon-remove\"></span> " + i.genename + "</button>"))
    table = ItemTablePanel(result, classes=['table', 'table-striped'])
    return render_template('panel_detail.html', panel_name=name, version=version,
                           panel_detail=table, genes=" ".join(sorted(set(genes))), form=form, add_form=add_form,
                           panel_id=id)


@app.route('/panels/edit', methods=['POST', 'GET'])
def edit_panel():
    if request.method == 'POST':
        panel_id = request.form["panel_id"]
        for v in request.form:
            if v.startswith("region"):
                value = int(request.form[v])
                region, region_id, intro, last, current_version, id, start, ext_5, end, ext_3, scope = v.split("_")
                if ext_5:
                    original_start = int(start) + int(ext_5)
                else:
                    original_start = start
                if ext_3:
                    original_end = int(end) + int(ext_3)
                else:
                    original_end = end
                if scope == "start":

                    if value != int(original_start):

                        print original_start
                        print value

                        extension_5 = int(value) - int(original_start)
                        check = s.query(models.Versions).filter_by(region_id=region_id,
                                                                   intro=int(current_version) + 1).count()
                        print v
                        if check > 0:
                            s.query(models.Versions).filter_by(region_id=region_id,
                                                               intro=int(current_version) + 1).update(
                                {models.Versions.extension_5: extension_5})
                            s.commit()
                        else:
                            s.query(models.Versions).filter_by(id=id).update({models.Versions.last: current_version})
                            s.commit()
                            v = models.Versions(intro=int(current_version) + 1, last=None, panel_id=int(panel_id),
                                                comment=None,
                                                extension_3=None, extension_5=int(extension_5),
                                                region_id=int(region_id))
                            s.add(v)
                            s.commit()
                if scope == "end":
                    if value != int(original_end):
                        print "hello"
                        extension_3 = int(value) - int(original_end)

                        check = s.query(models.Versions).filter_by(region_id=region_id,
                                                                   intro=int(current_version) + 1).count()
                        if check > 0:
                            s.query(models.Versions).filter_by(region_id=region_id,
                                                               intro=int(current_version) + 1).update(
                                {models.Versions.extension_3: extension_3})
                            s.commit()
                        else:
                            s.query(models.Versions).filter_by(id=id).update({models.Versions.last: current_version})
                            s.commit()
                            v = models.Versions(intro=int(current_version) + 1, last=None, panel_id=int(panel_id),
                                                comment=None,
                                                extension_3=extension_3, extension_5=None,
                                                region_id=int(region_id))
                            s.add(v)
                            s.commit()
    return edit_panel_page(panel_id=panel_id)


@app.route('/panels/delete/gene', methods=['POST'])
def remove_gene():
    s = scoped_session(db.session)
    form = RemoveGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
        panel_info = get_panel_edit(s, id, 1)
        ids = []
        for i in panel_info:
            if i.genename == gene:
                s.query(models.Versions).filter_by(id=i.id).update({models.Versions.last: i.current_version})
                ids.append(i.id)
    s.commit()
    return edit_panel_page(id)

@app.route('/panels/delete/gene', methods=['POST'])
def delete_region():
    pass
    return edit_panel_page(id)

@app.route('/panels/delete/add', methods=['POST'])
def add_gene():
    form = AddGene()
    if request.method == 'POST':
        id = form.data['panelId']
        gene = form.data['geneName']
    return edit_panel_page(id)


########################
# USERS
########################

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


########################
# PROJECTS
########################

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
def delete_project():
    u = db.session.query(models.Projects).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_projects()
