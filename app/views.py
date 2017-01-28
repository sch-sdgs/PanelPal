from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect
from flask_login import login_required, login_user, logout_user, current_user
from app.main import s,db, app
from functools import wraps
from app.forms import Login,Search
from app.queries import *
from mod_admin.queries import check_if_admin
from flask_table import Table, Col, LinkCol
from flask_login import LoginManager, UserMixin, \
    current_user
from app.activedirectory import UserAuthentication
import logging
from logging.handlers import TimedRotatingFileHandler
import inspect
import itertools


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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if check_if_admin(s,current_user.id) is False:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# def message(f):
#     @wraps(f)
#     def decorated_function(*args,**kwargs):
#         method = f.__name__
#         result=[]
#         if current_user.is_authenticated:
#             formatter = logging.Formatter('%(levelname)s|' + current_user.id + '|%(asctime)s|%(message)s')
#             handler.setFormatter(formatter)
#             app.logger.addHandler(handler)
#         else:
#             formatter = logging.Formatter('%(levelname)s|' +'anon' + '|%(asctime)s|%(message)s')
#             handler.setFormatter(formatter)
#             app.logger.addHandler(handler)
#         for i in request.args:
#             arg = request.args.get(i)
#             result.append(i)
#             result.append(arg)
#         for i in request.form:
#             arg = request.form[i]
#             result.append(i)
#             result.append(arg)
#         app.logger.info(method+"|"+"|".join(result))
#         return f(*args, **kwargs)
#     return decorated_function


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

class LinkColPrefTx(LinkCol):
    def td_contents(self, item, attr_list):
        if item["preftx"] is True:
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

# class ItemTableVirtualPanel(Table):
#     vp_name = Col('Name')
#     current_version = Col('Version')
#     status = LabelCol('Status')
#     edit = LinkCol('Edit', 'edit_panel_page', url_kwargs=dict(id='id'))
#     # todo make edit_vp_panel_page
#     # id = Col('Id')
#     make_live = LinkCol('Make Live', 'make_virtualpanel_live', url_kwargs=dict(id='id'))
#     delete = LinkCol('Delete', 'delete_virtualpanel', url_kwargs=dict(id='id'))


class ItemTableUsers(Table):
    username = Col('User')
    admin = Col('Admin')
    toggle_admin = LinkCol('Toggle Admin', 'toggle_admin', url_kwargs=dict(id='id'))

class ItemTableLocked(Table):

    name = Col('Panel')
    username = Col('Locked By')
    toggle_lock = LinkCol('Toggle Lock', 'toggle_locked', url_kwargs=dict(id='id'))

class ItemTableSearchTx(Table):
    id = Col('Transcript Accession')

class ItemTableSearchGene(Table):
    gene_name = Col('Gene')

class ItemTableSearchVPanels(Table):
    panel_name = LinkCol('Panel', 'view_panel', url_kwargs=dict(id='panel_id'), attr='panel_name')
    vpanel_name = LinkCol('Virtual Panel', 'view_vpanel', url_kwargs=dict(id='vpanel_id'), attr='vpanel_name')

class ItemTableSearchVPanelsTwo(Table):
    vpanel_name = LinkCol('', 'view_vpanel', url_kwargs=dict(id='vpanel_id'), attr='vpanel_name')

class ItemTableSearchPanels(Table):
    panel_name = LinkCol('', 'view_panel', url_kwargs=dict(id='panel_id'), attr='panel_name')

class ItemTableSearchProjects(Table):
    project_name = LinkCol('', 'view_panels', url_kwargs=dict(id='project_id'), attr='project_name')

class ItemTableSearchUsers(Table):
    username = Col('')

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
    test = s.query(Genes).filter_by(name=gene).first()
    if test is None:
        return False
    else:
        return True





# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
@app.context_processor
def logged_in():
    if current_user.is_authenticated:
        userid = current_user.id
        admin=check_if_admin(s,userid)

        #app.logger.basicConfig(format='%(levelname)s|'+ current_user.id+'|%(asctime)s|%(message)s')
        return {'logged_in': True, 'userid': userid,'admin':admin}
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
    result = s.query(Genes).filter(Genes.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@app.route('/autocomplete_tx', methods=['GET'])
def autocomplete_tx():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Tx).filter(Tx.accession.like("%" + value + "%")).all()
    data = [i.accession for i in result]
    return jsonify(matching_results=data)

@app.route('/autocomplete_panel', methods=['GET'])
def autocomplete_panel():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Panels).filter(Panels.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@app.route('/autocomplete_vp', methods=['GET'])
def autocomplete_vp():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(VirtualPanels).filter(VirtualPanels.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@app.route('/autocomplete_project', methods=['GET'])
def autocomplete_project():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Projects).filter(Projects.name.like("%" + value + "%")).all()
    data = [i.name for i in result]
    return jsonify(matching_results=data)

@app.route('/autocomplete_user', methods=['GET'])
def autocomplete_user():
    """
    this is the method for gene auto-completion - gets gene list from db and makes it into a json so that javascript can read it
    :return: jsonified gene list
    """
    value = str(request.args.get('q'))
    result = s.query(Users).filter(Users.username.like("%" + value + "%")).all()
    data = [i.username for i in result]
    return jsonify(matching_results=data)

########################
# PANELS
########################

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




@app.route("/logout")
@login_required
def logout():
    # todo unlock all users locked
    app.logger.info("logout")
    logout_user()
    form = Login()
    return render_template("login.html", form=form, message="You have logged out of PanelPal")


################
# SEARCH
################
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_for():
    form = Search()
    if request.method == 'GET':
        return render_template("search.html", form=form)
    else:
        type = request.form["tables"]
        term = request.form["search_term"]

        if type == "Genes":
            tx_result=[]
            gene_id = get_gene_id_from_name(s, term)
            tx = get_tx_by_gene_id(s, gene_id)

            for t in tx:
                tx_accession = {'id':t[1]}
                tx_result.append(tx_accession)
            table_one = ItemTableSearchTx(tx_result, classes=['table', 'table-striped'])

            vpanel_result = []
            vpanel = get_vpanel_by_gene_id(s, gene_id)
            vpanel_list = list(vpanel)

            if len(vpanel_list) > 0:
                for vp in vpanel_list:
                    vp_id = vp[0]
                    vp_name = vp[1]
                    broad_name = get_panel_by_vpanel_id(s, vp_id)
                    for b in broad_name:
                        vpanel_info = {'vpanel_name': vp_name, 'vpanel_id': vp_id, 'panel_name': b[0], 'panel_id': b[1]}
                        vpanel_result.append(vpanel_info)
                table_two = ItemTableSearchVPanels(vpanel_result, classes=['table', 'table-striped'])
            else:
                panel_results=[]
                panel = get_panel_by_gene_id(s, gene_id)
                for p in panel:
                    p_info = {'panel_name':p[1], 'panel_id':p[0]}
                    panel_results.append(p_info)
                table_two = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

            return render_template("search_results.html", genes_tx=table_one, genes_panels=table_two, term=term)

        if type == "Transcripts":
            tx_id = get_tx_id_from_name(s,term)
            gene = get_gene_from_tx(s, tx_id)
            gene_result=[]

            for g in gene:
                gene_info = {'gene_name':g[0]}
                gene_id = g[1]
                gene_result.append(gene_info)
            table_one = ItemTableSearchGene(gene_result, classes=['table', 'table-striped'])

            vpanel_result = []
            vpanel = get_vpanel_by_gene_id(s, gene_id)
            vpanel_list = list(vpanel)
            if len(vpanel_list) > 0:
                for vp in vpanel_list:
                    vp_id = vp[0]
                    vp_name = vp[1]
                    broad_name = get_panel_by_vpanel_id(s, vp_id)
                    for b in broad_name:
                        vpanel_info = {'vpanel_name': vp_name, 'vpanel_id': vp_id, 'panel_name': b[0], 'panel_id': b[1]}
                        vpanel_result.append(vpanel_info)
                table_two = ItemTableSearchVPanels(vpanel_result, classes=['table', 'table-striped'])
            else:
                panel_results=[]
                panel = get_panel_by_gene_id(s, gene_id)
                for p in panel:
                    p_info = {'panel_name':p[1], 'panel_id':p[0]}
                    panel_results.append(p_info)
                table_two = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

            return render_template("search_results.html", tx_genes=table_one, tx_panels=table_two, term=term)

        if type == "Panels":
            panel = get_panel_id_by_name(s,term)
            panel_results=[]
            for p in panel:
                panel_id = p[0]
                project_id = p[1]
                panel_info = {'panel_name': term, 'panel_id': panel_id}
                panel_results.append(panel_info)
            table_one = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

            project = get_project_name(s,project_id)
            project_results = [{'project_name': project, 'project_id': project_id}]
            table_two = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

            vpanels = get_virtual_panels_by_panel_id(s, panel_id)
            vpanel_results=[]
            for vp in vpanels:
                vpanel_info={'vpanel_name': vp[6], 'vpanel_id': vp[0]}
                vpanel_results.append(vpanel_info)
            table_three = ItemTableSearchVPanelsTwo(vpanel_results, classes=['table', 'table-striped'])

            users = get_user_rel_by_project_id(s, project_id)
            user_results = []
            for u in users:
                user_info = {'username': u[0]}
                user_results.append(user_info)
            table_four = ItemTableSearchUsers(user_results, classes=['table', 'table-striped'])


            version = get_current_version(s, panel_id)
            genes = get_genes_by_panelid(s, panel_id, version)
            gene_results=[]
            for g in genes:
                gene_info={'gene_name': g[0]}
                gene_results.append(gene_info)
            table_five = ItemTableSearchGene(gene_results, classes=['table', 'table-striped'])

            return render_template("search_results.html", panels_panels=table_one, panels_projects=table_two, panels_vpanels=table_three, \
                                   panels_users=table_four, panels_genes=table_five, term=term)


        if type == "VPanels":
            vpanel_id = get_vpanel_id_by_name(s, term)
            for vp in vpanel_id:
                vpanel_id = vp[0]
                vpanel_results=[{'vpanel_name': term, 'vpanel_id': vpanel_id}]
            table_one = ItemTableSearchVPanelsTwo(vpanel_results, classes=['table', 'table-striped'])


            panel = get_panel_by_vpanel_id(s, vpanel_id)
            for p in panel:
                panel_id = p[1]
                panel_results=[{'panel_name': p[0], 'panel_id': panel_id}]
            table_two = ItemTableSearchPanels(panel_results, classes=['table', 'table-striped'])

            project_id = get_project_id_by_panel_id(s, panel_id)
            project_name = get_project_name(s, project_id)
            project_results=[{'project_name': project_name, 'project_id': project_id}]
            table_three = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

            users = get_user_rel_by_project_id(s, project_id)
            user_results = []
            for u in users:
                user_info = {'username': u[0]}
                user_results.append(user_info)
            table_four = ItemTableSearchUsers(user_results, classes=['table', 'table-striped'])

            version = get_current_vpanel_version(s, vpanel_id)
            genes = get_genes_by_vpanelid(s, panel_id, version)
            gene_results = []
            for g in genes:
                gene_info = {'gene_name': g[0]}
                gene_results.append(gene_info)
            table_five = ItemTableSearchGene(gene_results, classes=['table', 'table-striped'])

            return render_template("search_results.html", vpanels_vpanels=table_one, vpanels_panels=table_two, vpanels_projects=table_three, \
                                   vpanels_users=table_four, vpanels_genes=table_five, term=term)

        if type == "Projects":
            project_id = get_project_id_by_name(s, term)
            project_results = [{'project_name': term, 'project_id': project_id}]
            table_one = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

            panels = get_panels_by_project_id(s, project_id)
            panel_results = []
            for p in panels:
                panel_id = p[4]
                panel_name = p[2]
                vpanels = get_virtual_panels_by_panel_id(s, panel_id)
                vp_list = list(vpanels)
                count=1
                if len(vp_list)>0:
                    for vp in vp_list:
                        vp_id = vp[0]
                        vp_name = vp[6]
                        if count == 1:
                            panel_info = {'panel_name': panel_name, 'panel_id': panel_id, 'vpanel_name': vp_name, 'vpanel_id': vp_id}
                            panel_results.append(panel_info)
                            count=2
                        else:
                            panel_info = {'panel_name': '', 'panel_id': '', 'vpanel_name': vp_name, 'vpanel_id': vp_id}
                            panel_results.append(panel_info)
                else:
                    panel_info = {'panel_name': panel_name, 'panel_id': panel_id, 'vpanel_name': '', 'vpanel_id': ''}
                    panel_results.append(panel_info)
            table_two = ItemTableSearchVPanels(panel_results, classes=['table', 'table-striped'])

            users = get_user_rel_by_project_id(s, project_id)
            user_results = []
            for u in users:
                user_info = {'username': u[0]}
                user_results.append(user_info)
            table_three = ItemTableSearchUsers(user_results, classes=['table', 'table-striped'])

            return render_template("search_results.html", projects_project=table_one, projects_panels=table_two, projects_users=table_three, term=term)


        if type == "Users":
            projects = get_projects_by_user(s, term)
            project_results=[]
            for p in projects:
                project_info = {'project_id': p[0], 'project_name': p[1]}
                project_results.append(project_info)
            table_one = ItemTableSearchProjects(project_results, classes=['table', 'table-striped'])

            return render_template("search_results.html", users_projects=table_one, term=term)




