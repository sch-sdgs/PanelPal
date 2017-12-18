from collections import OrderedDict

from app.mod_admin.queries import *
from app.mod_panels.queries import  unlock_panel_query
from queries import check_if_admin, get_user_id_by_username
from flask import Blueprint
from flask import render_template, request, url_for, redirect
from flask_login import login_required, login_user, logout_user, current_user, UserMixin
from functools import wraps

from app.panel_pal import s, app
from app.activedirectory import UserAuthentication
from app.mod_projects.queries import get_all_projects, get_projects_by_user, remove_user_project_rel_no_id, add_user_project_rel
from flask_table import Table, Col, LinkCol
from forms import UserForm
from queries import create_user, toggle_admin_query





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