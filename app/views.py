from flask import Blueprint
from flask import render_template, request, url_for, jsonify, redirect
from flask_login import login_required, login_user, logout_user, current_user
from app.panel_pal import s,db, app
from functools import wraps
from app.forms import Login
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
        if item["locked"] is None and item["permission"] is True and item["status"] is False:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'


class LinkColConditional(LinkCol):
    def td_contents(self, item, attr_list):
        if item["permission"] is True:
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






