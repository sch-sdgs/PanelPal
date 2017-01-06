from flask import render_template, request, flash, url_for, Markup, jsonify, redirect, Response
from sqlalchemy.orm import scoped_session
from app import app, s, models, activedirectory
from collections import OrderedDict
from functools import wraps
import json
from app import app, s, models
from app.queries import *
from flask_table import Table, Col, LinkCol
from forms import ProjectForm, RemoveGene, AddGene, CreatePanel, Login, PrefTxCreate, EditPermissions, CreateVirtualPanel, SelectVPGenes
from flask.ext.login import LoginManager, UserMixin, \
    login_required, login_user, logout_user, current_user

app.secret_key = 'development key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, id, password=None):
        self.id = id
        self.password = password

    def is_authenticated(self, s, id, password):
        validuser = get_user_by_username(s, id)
        if len(list(validuser)) == 0:
            return False
        else:
            check_activdir = activedirectory.UserAuthentication().authenticate(id, password)

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


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

class NumberCol(Col):
    def __init__(self, name, valmin=False, attr=None, attr_list=None, **kwargs):
        self.valmin = valmin
        super(NumberCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        """
        special td contents for editing a panel - so includes form input fields etc
        :param item:
        :param attr_list:
        :return:
        """
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


class LockCol(Col):
    def __init__(self, name, attr=None, attr_list=None, **kwargs):
        super(LockCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        print "HELLO"
        print item
        if item["locked"] is not None:
            username = get_username_by_user_id(s, item["locked"])
            return '<center><span class="glyphicon glyphicon-lock"  data-toggle="tooltip" data-placement="bottom" title="Locked by: ' + username + '" aria-hidden="true"></span></center>'
        else:
            return ''

class LinkColLive(LinkCol):

    def td_contents(self, item, attr_list):
        if item["conditional"] is True and item["status"] is False:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'

class LinkColConditional(LinkCol):

    def td_contents(self, item, attr_list):
        if item["conditional"] is True:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'

class LabelCol(Col):
    def __init__(self, name, valmin=False, attr=None, attr_list=None, **kwargs):

        self.valmin = valmin
        super(LabelCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)

    def td_contents(self, item, attr_list):
        """
        This is the contents of a status column to indicate whether a panel is live or has changes

        :param item:
        :param attr_list:
        :return:
        """
        if self.from_attr_list(item, attr_list):
            type = "success"
            status = "Live"
        else:
            type = "danger"
            status = "Changes"

        return '<p><span class="label label-{type}">{status}</span></p>'.format(type=type, status=status)


class ItemTable(Table):
    username = Col('Username')
    id = Col('Id')
    delete = LinkCol('Delete', 'delete_users', url_kwargs=dict(id='id'))


class ItemTablePermissions(Table):
    # username = Col('Username')
    username = Col('User')
    delete = LinkCol('Remove', 'remove_permission', url_kwargs=dict(userid='user_id',projectid='project_id'))


class ItemTableVirtualPanel(Table):
    vp_name = Col('Name')
    current_version = Col('Version')
    status = LabelCol('Status')
    edit = LinkCol('Edit', 'edit_panel_page', url_kwargs=dict(id='id'))
    # todo make edit_vp_panel_page
    # id = Col('Id')
    make_live = LinkCol('Make Live', 'make_virtualpanel_live', url_kwargs=dict(id='id'))
    delete = LinkCol('Delete', 'delete_virtualpanel', url_kwargs=dict(id='id'))


class ItemTableProject(Table):
    name = Col('Name')
    view = LinkCol('View Panels', 'view_panels', url_kwargs=dict(id='id'))
    pref_tx = LinkCol('View Preferred Tx', 'view_preftx', url_kwargs=dict(id='id'))
    permissions = LinkColConditional('Edit Permissions', 'edit_permissions', url_kwargs=dict(id='id'))
    # make = LinkCol('Make Panel', '', url_kwargs=dict())
    delete = LinkColConditional('Delete', 'delete_project', url_kwargs=dict(id='id'))


class ItemTablePanels(Table):
    panelname = Col('Name')
    current_version = Col('Stable Version')
    view_panel = LinkCol('View Panel', 'view_panel', url_kwargs=dict(id='panelid'))
    edit = LinkColConditional('Edit Panel','edit_panel_page',url_kwargs=dict(panelid='panelid'))
    view = LinkCol('View Virtual Panels', 'view_virtual_panels', url_kwargs=dict(id='panelid'))
    locked = LockCol('Locked')
    status = LabelCol('Status')
    make_live = LinkColLive('Make Live', 'make_live', url_kwargs=dict(id='panelid'))
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))

class ItemTableVPanels(Table):
    vp_name = Col('Name')
    current_version = Col('Stable Version')
    view_panel = LinkCol('View Panel', 'view_vpanel', url_kwargs=dict(id='id'))
    edit = LinkColConditional('Edit Panel','edit_panel_page',url_kwargs=dict(id='id'))
    locked = LockCol('Locked')
    status = LabelCol('Status')
    make_live = LinkColLive('Make Live', 'make_virtualpanel_live', url_kwargs=dict(id='id'))
    # delete = LinkCol('Delete', 'delete_study', url_kwargs=dict(id='studyid'))



class ItemTablePanelView(Table):
    allow_sort = False
    chrom = Col('Chromosome')
    start = Col('Start')
    end = Col('End')
    number = Col('Exon')
    accession = Col('Accession')
    genename = Col('Gene')

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('edit_panel_page', sort=col_key, direction=direction)

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


class ItemTablePrefTx(Table):
    genename = Col('Gene Name')
    accession = Col('Accession')
    tx_start = Col('Transcript Start')
    tx_end = Col('Transcript End')
    strand = Col('Strand')


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


def isgene(s, gene):
    """
    checks if a gene is in refflad

    :param s: db session
    :param gene: gene name
    :return: true or false
    """
    test = s.query(models.Genes).filter_by(name=gene).first()
    if test is None:
        return False
    else:
        return True


def check_panel_status(s, id):
    """
    checks the status of a panel - i.e. whether it is live or not live (it has uncommited changes)

    :param s: db session
    :param id: panel id
    :return: true - panel is live or false - panel has changes
    """
    panels = check_panel_status_query(s, id)
    status = True
    for i in panels:
        if i.intro > i.current_version:
            status = False
            break
        if i.last is not None:
            if i.last == i.current_version:
                status = False
                break

    return status


def check_virtualpanel_status(s, id):
    """
    checks the status of a panel - i.e. whether it is live or not live (it has uncommited changes)

    :param s: db session
    :param id: panel id
    :return: true - panel is live or false - panel has changes
    """
    panels = check_virtualpanel_status_query(s, id)
    status = True
    for i in panels:
        if i.intro > i.current_version:
            status = False
            break
        if i.last is not None:
            if i.last == i.current_version:
                status = False
                break

    return status

@app.context_processor
def logged_in():
    if current_user.is_authenticated:
        userid = current_user.id
        return {'logged_in': True, 'userid': userid}
    else:
        return {'logged_in': False}


@app.route('/')
def index():
    return render_template('home.html', panels=3)
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(models.Genes).filter(models.Genes.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    print data
    return jsonify(matching_results=data)


# test=None
#
# def lock_check(f):
#     @wraps(f)
#     def decorated_function(*args,**kwargs):
#         if test is None:
#             return redirect('/')
#         return f(*args, **kwargs)
#     return decorated_function


########################
# PANELS
########################

@app.route('/download')
@login_required
def download_as_bed():
    bed = "test\ttest\ttest"
    return Response(
        bed,
        mimetype='test/plain',
        headers={"Content-disposition":
                 "attachment; filename=test.bed"}
    )


@app.route('/panels', methods=['GET', 'POST'])
@login_required
# @lock_check
def view_panels(id=None):
    """
    method to view panels, if project ID given then only return panels from that project
    matt
    :param id: project id
    :return: rendered template panels.html
    """
    if not id:
        id = request.args.get('id')
    if id:
        panels = get_panels_by_project_id(s, id)
    else:
        panels = get_panels(s)
    result = []
    project_name = "All"
    for i in panels:
        row = dict(zip(i.keys(), i))
        status = check_panel_status(s, row["panelid"])
        row["status"] = status
        permission = check_user_has_permission(s, current_user.id, row["projectid"])
        locked = check_if_locked_by_user(s, current_user.id,row["panelid"])
        row["conditional"] = None
        if permission is True and locked is True:
            row["conditional"] = True
        if permission is True and locked is False:
            row["conditional"] = False
        if permission is False and locked is False:
            row["conditional"] = False

        print row
        if id:
            project_name = row['projectname']
        # if check_user_has_permission(s, current_user.id, row["projectid"]):
        #     result.append(row)
        result.append(row)
    table = ItemTablePanels(result, classes=['table', 'table-striped'])
    return render_template('panels.html', panels=table, project_name=project_name)

@app.route('/panel', methods=['GET', 'POST'])
@login_required
def view_panel():
    id = request.args.get('id')
    if id:
        status = check_panel_status(s, id)
        if not status:
            message = "This panel has changes which cannot be viewed here as they have not been made live yet, if you have permission you can view these by editing the panel"
        else:
            message = None
        panel_details = get_panel_details_by_id(s,id)
        for i in panel_details:
            version = i.current_version
            panel_name = i.name
        panel = get_panel_by_id(s, id)
        project_id = get_project_id_by_panel_id(s,id)
        print project_id
        result=[]
        rows = list(panel)
        if len(rows) != 0:
            bed = ''
            for i in rows:
                row = dict(zip(i.keys(), i))
                # status = check_panel_status(s, row["panelid"])
                # row["status"] = status
                result.append(row)
                panel_name=row["name"]
                version=row["current_version"]
            table = ItemTablePanelView(result, classes=['table', 'table-striped'])
        else:
            table = ""
            message = "This Panel has no regions yet & may also have chnages that have not been made live"
            bed = 'disabled'

        if check_user_has_permission(s,current_user.id,project_id):
            edit = ''
        else:
            edit = 'disabled'
        return render_template('panel_view.html', panel=table, panel_name=panel_name, edit=edit, bed=bed, version=version, panel_id=id, message=message)

    else:
        return redirect(url_for('view_panels'))

@app.route('/vpanel', methods=['GET', 'POST'])
@login_required
def view_vpanel():
    id = request.args.get('id')
    if id:
        status = check_virtualpanel_status(s, id)
        if not status:
            message = "This panel has changes which cannot be viewed here as they have not been made live yet, if you have permission you can view these by editing the panel"
        else:
            message = None
        panel_details = get_vpanel_details_by_id(s,id)
        for i in panel_details:
            version = i.current_version
            panel_name = i.name
            project_id = i.project_id
        panel = get_vpanel_by_id(s, id)
        result=[]
        rows = list(panel)
        if len(rows) != 0:
            bed = ''
            for i in rows:
                row = dict(zip(i.keys(), i))
                # status = check_panel_status(s, row["panelid"])
                # row["status"] = status
                result.append(row)
                panel_name=row["name"]
                version=row["current_version"]
            table = ItemTablePanelView(result, classes=['table', 'table-striped'])
        else:
            table = ""
            message = "This Panel has no regions yet & may also have chnages that have not been made live yet"
            bed = 'disabled'

        if check_user_has_permission(s,current_user.id,project_id):
            edit = ''
        else:
            edit = 'disabled'
        return render_template('panel_view.html', panel=table, panel_name=panel_name, edit=edit, bed=bed, version=version, panel_id=id, message=message, scope='Virtual')

    else:
        return redirect(url_for('view_panels'))

@app.route('/panels/create', methods=['GET', 'POST'])
@login_required
def create_panel():
    form = CreatePanel()
    if request.method == 'POST':
        # if form.validate() == False:
        #     flash('All fields are required.')
        #     return render_template('panel_create.html', form=form)
        # else:
        panelname = request.form["panelname"]
        project = request.form["project"]
        genesraw = request.form["listgenes"]
        genes = genesraw.rstrip(',').split(",")

        result = []
        for gene in genes:
            test = isgene(s, gene)
            result.append(test)

        if False not in result:
            test_panel = s.query(models.Panels).filter_by(name=panelname).first()
            if test_panel is not None:
                return render_template('panel_create.html', form=form, message="Panel Name Exists")
            else:
                id = create_panel_query(s, project, panelname)

                for gene in genes:
                    add_genes_to_panel(s, id, gene)
                return redirect(url_for('edit_panel_page', id=id))
        else:
            return render_template('panel_create.html', form=form, message="One or more Gene Name(s) Invalid")

    elif request.method == 'GET':
        return render_template('panel_create.html', form=form)


@app.route('/panels/live', methods=['GET', 'POST'])
@login_required
def make_live():
    """
    given a panel id this method makes a panel live

    :return: redirection to view panels
    """
    panelid = request.args.get('id')
    current_version = get_current_version(s, panelid)
    new_version = current_version + 1
    make_panel_live(s, panelid, new_version,current_user.id)

    return redirect(url_for('view_panels'))

@app.route('/panels/unlock')
def unlock_panel():
    panelid = request.args.get('panelid')
    unlock_panel_query(s,panelid)

    return redirect(url_for('view_panels'))

@app.route('/panels/edit')
@login_required
def edit_panel_page(panel_id=None):
    id = request.args.get('panelid')
    lock_panel(s, current_user.id, id)
    if id is None:
        id = panel_id
    panel_info = s.query(models.Panels, models.Projects).join(models.Projects).filter(models.Panels.id == id).values(
        models.Panels.current_version,
        models.Panels.name,
        models.Panels.locked
    )
    print panel_info
    for i in panel_info:
        print i.current_version
        version = i.current_version
        name = i.name

    panel = get_panel_edit(s, id=id, version=version)

    form = RemoveGene(panelId=id)
    print "PANEL ID" + str(id)
    add_form = AddGene(panelIdAdd=id)
    print add_form.panelIdAdd

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
    return render_template('panel_edit.html', panel_name=name, version=version,
                           panel_detail=table, genes=" ".join(sorted(set(genes))), form=form, add_form=add_form,
                           panel_id=id)


@app.route('/panels/edit', methods=['POST', 'GET'])
@login_required
def edit_panel():
    if request.method == 'POST':
        panel_id = request.form["panel_id"]
        for v in request.form:
            print v
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
@login_required
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
                # todo add if in here - if the gene is not already in a live panel it is okay to delete completely
                s.query(models.Versions).filter_by(id=i.id).update({models.Versions.last: i.current_version})
                ids.append(i.id)
    s.commit()
    return edit_panel_page(id)


@app.route('/panels/delete/gene', methods=['POST'])
@login_required
def delete_region():
    pass
    return edit_panel_page(id)


@app.route('/panels/delete/add', methods=['POST'])
@login_required
def add_gene():
    """
    adds a gene to a panel
    :return: edit panel page
    """
    form = AddGene()
    if request.method == 'POST':
        id = form.data['panelIdAdd']
        gene = form.data['genes']
        if isgene(s, gene):
            add_genes_to_panel(s, id, gene)
    return edit_panel_page(id)


########################
# PROJECTS
########################

@app.route('/projects')
@login_required
def view_projects(delete=False, project_name=None, project_id=None):
    projects = models.Projects.query.all()
    result = []
    for i in projects:
        row = row2dict(i)
        row['conditional'] = check_user_has_permission(s, current_user.id, row["id"])
        # if check_user_has_permission(s, current_user.id, row["id"]):
        #     result.append(row)
        result.append(row)
    table = ItemTableProject(result, classes=['table', 'table-striped'])
    return render_template('projects.html', projects=table, delete=delete, project_name=project_name,
                           project_id=project_id)


@app.route('/projects/add', methods=['GET', 'POST'])
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


@app.route('/projects/delete', methods=['GET', 'POST'])
@login_required
def delete_project():
    # todo display a modal here with "do you really want to delete?" message
    id = request.args.get('id')
    if request.args.get('check'):
        print "I AM DELETEING"
        u = s.query(models.Projects).filter_by(id=id).first()
        s.delete(u)
        s.commit()
        return view_projects()
    else:
        return view_projects(delete=True, project_name="Test", project_id=id)


#################
# VIRTUAL PANELS
################



@app.route('/virtualpanels')
@login_required
def view_virtual_panels(id=None):
    """
       method to view panels, if project ID given then only return panels from that project
       matt
       :param id: project id
       :return: rendered template panels.html
       """
    if not id:
        id = request.args.get('id')
    if id:
        panels = get_virtual_panels_by_panel_id(s, id)
    else:
        panels = get_virtual_panels_simple(s)
    result = []
    panel_name = "Virtual"
    for i in panels:
        row = dict(zip(i.keys(), i))
        print row
        status = check_virtualpanel_status(s, row["id"])
        row["status"] = status
        permission = check_user_has_permission(s, current_user.id, row["projectid"])
        locked = check_if_locked_by_user(s, current_user.id, row["panelid"])
        row["conditional"] = None
        if permission is True and locked is True:
            row["conditional"] = True
        if permission is True and locked is False:
            row["conditional"] = False
        if permission is False and locked is False:
            row["conditional"] = False

        print row
        if id:
            panel_name = row['panelname'] + ' Virtual'
        # if check_user_has_permission(s, current_user.id, row["projectid"]):
        #     result.append(row)
        result.append(row)
    table = ItemTableVPanels(result, classes=['table', 'table-striped'])
    return render_template('panels.html', panels=table, project_name=panel_name, message='Virtual Panels are locked if their parent panel is being edited')



    # if not id:
    #     print('request')
    #     id = request.args.get('id')
    # print(id)
    # if id:
    #     print('by id')
    #     result = get_virtual_panels_by_panel_id(s, id)
    # else:
    #     result = get_virtual_panels_simple(s)
    # all_results = []
    # print result
    # for i in result:
    #     print i
    #     row = dict(zip(i.keys(), i))
    #     status = check_virtualpanel_status(s, row["id"])
    #     row["status"] = status
    #     if check_user_has_permission(s, current_user.id, row["projectid"]):
    #         all_results.append(row)
    #
    # table = ItemTableVirtualPanel(all_results, classes=['table', 'table-striped'])
    # return render_template("virtualpanels.html", virtualpanels=table)

@app.route('/virtualpanels/create', methods=['GET', 'POST'])
@login_required
def create_virtual_panel():
    """

    :return:
    """
    form = CreateVirtualPanel()

    if request.method == "POST":
        name = request.form["vpanelname"]
        testvpanel = s.query(models.VirtualPanels).filter_by(name=name).first()
        print(testvpanel)
        if testvpanel is not None:
            return render_template('virtualpanels_create.html', form=form, message='Virtual panel name exists')
        else:
            panel_id = request.form["panel"]
            create_virtualpanel_query(s, name)
            return redirect(url_for('select_vp_genes', vp=name, panel=panel_id))
    elif request.method == 'GET':
        return render_template('virtualpanels_create.html', form=form)


@app.route('/virtualpanels/select', methods=['GET', 'POST'])
@login_required
def select_vp_genes():
    """

    :return:
    """
    form = SelectVPGenes()

    if request.method == "POST":
        pass
    else:
        vp = request.args.get("vp")
        panel_id = request.args.get("panel")
        current_version = get_current_version(s, panel_id)
        genes = get_genes_by_panelid(s, panel_id, current_version)
        return render_template('virtualpanels_selectgenes.html', form=form, vp_name=vp, panel_id=panel_id, genes=genes)

@app.route('/virtualpanels/live', methods=['GET', 'POST'])
def make_virtualpanel_live():
    """
    given a panel id this method makes a panel live

    :return: redirection to view panels
    """
    panelid = request.args.get('id')
    current_version = get_current_vp_version(s, panelid)
    new_version = current_version + 1
    make_vp_panel_live(s, panelid, new_version)

    return redirect(url_for('view_virtual_panels'))

@app.route('/virtualpanels/delete', methods=['GET', 'POST'])
def delete_virtualpanel():
    u = db.session.query(models.VirtualPanels).filter_by(id=request.args.get('id')).first()
    db.session.delete(u)
    db.session.commit()
    return view_virtual_panels()

#################
# USER LOGIN
#################

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login(next=request.args.get('next'))
    if request.method == 'GET':
        return render_template("login.html", form=form)
    elif request.method == 'POST':
        user = User(form.data["username"], password=form.data["password"])
        result = user.is_authenticated(s, id=form.data["username"], password=form.data["password"])
        if result:
            login_user(user)
            if form.data["next"] != "":
                return redirect(form.data["next"])
            else:
                return redirect(url_for('index'))
        else:
            return render_template("login.html", form=form, modifier="Oh Snap!", message="Wrong username or password")


@app.route("/edit_permissions", methods=['GET', 'POST'])
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

@app.route("/remove_permissions")
def remove_permission():
    panel_id = request.args.get('panelid')
    project_id = request.args.get('projectid')
    if check_user_has_permission(s, current_user.id, project_id):
        pass

@app.route("/logout")
@login_required
def logout():
    # todo unlock all users locked
    logout_user()
    form = Login()
    return render_template("login.html", form=form, message="You have logged out of PanelPal")


#################
# PREFTX
#################

@app.route('/preftx')
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
            row = dict(zip(i.keys(), i))
            all_results.append(row)
        print all_results
        table = ItemTablePrefTx(all_results, classes=['table', 'table-striped'])
    return render_template("preftx.html", preftx=table, project_name=project)


@app.route('/preftx/create', methods=['GET', 'POST'])
@login_required
def create_preftx():
    id = request.args.get('id')
    if request.method == 'GET':
        result = get_genes_by_projectid(s=s, projectid=id)
        genes = {}
        for i in result:
            print i.genename
            if i.genename not in genes:
                genes[i.genename] = list()
                genes[i.genename].append((i.txid, i.accession))
            else:
                genes[i.genename].append((i.txid, i.accession))

        list_of_forms = []
        for gene in genes:
            form = PrefTxCreate(request.form)
            form.gene.choices = genes[gene]
            form.gene.name = gene
            list_of_forms.append(form)

        print list_of_forms
        return render_template("preftx_create.html", genes=genes, list_of_forms=list_of_forms, project_id=id)

    elif request.method == 'POST':
        print request.form
        tx_ids = []
        for i in request.form:
            print i
            if i == "project_id":
                project_id = request.form["project_id"]
            else:
                tx_ids.append(request.form[i])

        add_preftxs_to_panel(s, project_id, tx_ids)
        return redirect(url_for('view_preftx', id=project_id))


####
# API
######

class ChrSorter():
    def __init__(self):
        pass

    @staticmethod
    def lt_helper(a):
        """
        helper to sort chromosmes properly

        :param a: sort object
        :return:
        """
        try:
            return int(a)
        except ValueError:
            if a == "X":
                return 24
            elif a == "Y":
                return 25
            elif a == "MT" or a == "M":
                return 26
            else:
                return 27

    @staticmethod
    def __lt__(a, b):
        """
        run the chromosome sort helper

        :param a:
        :param b:
        :return: proper sorted chromosomes
        """
        return cmp(ChrSorter.lt_helper(a), ChrSorter.lt_helper(b))


from flask_restful_swagger import swagger
from flask_restful import Resource, Api, reqparse, fields, marshal
from sqlalchemy.ext.serializer import loads, dumps

# app = Flask(__name__)
# app.config['BUNDLE_ERRORS'] = True

api = swagger.docs(Api(app), apiVersion='0.0', description="Test PanelPal API")

region_fields = {
    'start': fields.Integer,
    'end': fields.Integer,
    'chrom': fields.String,
    'annotation': fields.String
}

details_fields = {
    'version': fields.Integer,
    'panel': fields.String
}

panel_fields = {
    'details': fields.Nested(details_fields),
    'regions': fields.List(fields.Nested(region_fields))

}

#todo - need to add extensions from db here
def region_result_to_json(data,extension=0):
    args = request.args
    if 'extension' in args:
        extension = int(args["extension"])
    else:
        extension = 0
    result = dict()
    result['details'] = dict()
    result['regions'] = list()
    regions = dict()
    for i in data:
        region = dict()
        if i.Versions.extension_5 is not None:
            region['start'] = i.Regions.start - extension + i.Versions.extension_5
        else:
            region['start'] = i.Regions.start - extension
        if i.Versions.extension_3 is not None:
            region['end'] = i.Regions.end + extension + i.Versions.extension_3
        else:
            region['end'] = i.Regions.end + extension
        region["annotation"] = "ex" + str(i.Exons.number) + "_" + i.Genes.name + "_" + str(i.Tx.accession)
        if i.Regions.chrom.replace('chr', '') not in regions:
            regions[i.Regions.chrom.replace('chr', '')] = list()
        regions[i.Regions.chrom.replace('chr', '')].append(region)

    for i in sorted(regions, cmp=ChrSorter.__lt__):

        for details in regions[i]:
            region = dict()
            region["chrom"] = "chr" + str(i)
            region["start"] = details["start"]
            region["end"] = details["end"]
            region["annotation"] = details["annotation"]
            result['regions'].append(region)

    return result


@api.representation('application/json')
def output_json(data, code, headers=None):
    #todo marshal breaks swagger here - swaggermodels?
    resp = app.make_response(json.dumps(data))
    resp.headers.extend(headers or {})
    return resp


parser = reqparse.RequestParser()


# @app.errorhandler(404)
# def not_found(error=None):
#     message = {
#             'status': 404,
#             'message': 'Not Found: ' + request.url,
#     }
#     resp = jsonify(message)
#     resp.status_code = 404
#
#     return resp

class Panels(Resource):
    @swagger.operation(
        notes='Gets a JSON of all regions in the panel - this is equivalent to the broad panel',
        responseClass='x',
        nickname='broad',
        parameters=[
        ],
        responseMessages=[
            {
                "code": 201,
                "message": "Created. The URL of the created blueprint should be in the Location header"
            },
            {
                "code": 405,
                "message": "Invalid input"
            }
        ]
    )
    def get(self, name, version):
        result = get_panel_api(s, name, version)
        result_json = region_result_to_json(result.panel)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp

class VirtualPanels(Resource):
    @swagger.operation(
        notes='Gets a JSON of regions in a virtual panel - this is equivalent to the small panel',
        responseClass='x',
        nickname='small',
        parameters=[
            {
                "name": "extension",
                "paramType": "query",
                "required": False,
                "allowMultiple": False,
                "dataType": "integer"
            }
        ],
        responseMessages=[
            {
                "code": 201,
                "message": "Created. The URL of the created blueprint should be in the Location header"
            },
            {
                "code": 405,
                "message": "Invalid input"
            }
        ]
    )
    def get(self, name, version):
        result = get_vpanel_api(s, name, version)
        result_json = region_result_to_json(result.panel)
        result_json["details"]["panel"] = name
        result_json["details"]["version"] = int(result.current_version)
        resp = output_json(result_json, 200)
        resp.headers['content-type'] = 'application/json'
        return resp

# class Exonic(Resource):
#     @swagger.operation(
#         notes='Gets a JSON of regions in a virtual panel and adjusts for "exnoic" - equivalent to the exon file',
#         responseClass='x',
#         nickname='small',
#         parameters=[
#         ],
#         responseMessages=[
#             {
#                 "code": 201,
#                 "message": "Created. The URL of the created blueprint should be in the Location header"
#             },
#             {
#                 "code": 405,
#                 "message": "Invalid input"
#             }
#         ]
#     )
#     def get(self, name, version):
#         result = get_exonic_api(s, name, version)
#         result_json = region_result_to_json(result.panel,scope="exonic")
#         result_json["details"]["panel"] = name
#         result_json["details"]["version"] = int(result.current_version)
#         resp = output_json(result_json, 200)
#         resp.headers['content-type'] = 'application/json'
#         return resp

api.add_resource(Panels, '/api/panel/<string:name>/<string:version>', )
api.add_resource(VirtualPanels, '/api/virtualpanel/<string:name>/<string:version>', )
#api.add_resource(Exonic, '/api/exonic/<string:name>/<string:version>', )

