from flask import render_template, request, url_for, jsonify, redirect
from app.main import s
from collections import OrderedDict
from app.queries import *
from flask_table import Table, Col, LinkCol
from forms import UserForm
from flask.ext.login import login_required, current_user
from flask import Blueprint
from app.views import admin_required

class ItemTableUsers(Table):
    username = Col('User')
    admin = Col('Admin')
    toggle_admin = LinkCol('Toggle Admin', 'admin.toggle_admin', url_kwargs=dict(id='id'))

class ItemTableLocked(Table):

    name = Col('Panel')
    username = Col('Locked By')
    toggle_lock = LinkCol('Toggle Lock', 'admin.toggle_locked', url_kwargs=dict(id='id'))

admin = Blueprint('admin', __name__, template_folder='templates')

@admin.route('/admin/user',methods=['GET', 'POST'])
@login_required
@admin_required
def user_admin():
    form = UserForm()
    message=None
    if request.method == 'POST':
        username = request.form["name"]
        if check_if_admin(s,current_user.id):
            create_user(s,username)
            message = "Added user: " + username
        else:
            return render_template('users.html', form=form,message="You can't do that")
    users = get_users(s)
    result = []
    for i in users:
        if i.username != current_user.id:
            row = dict(zip(i.keys(), i))
            result.append(row)
    table = ItemTableUsers(result, classes=['table', 'table-striped'])
    return render_template('users.html',form=form,table=table,message=message)

@admin.route('/panels/add_pref_tx', methods=['POST'])
@login_required
def add_pref_tx():
    """

    :return:
    """
    gene_id = request.args.get('gene_id')
    tx = get_tx_by_gene_id(s, gene_id)
    return jsonify(tx)

@admin.route('/admin/user/admin',methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_admin():
    user_id=request.args.get('id')
    toggle_admin_query(s,user_id)
    return redirect(url_for('admin.user_admin'))

@admin.route('/admin/locked/toggle',methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_locked():
    panel_id=request.args.get('id')
    unlock_panel_query(s,panel_id)
    return view_locked(message="Panel Unlocked")

@admin.route('/admin/logs',methods=['GET', 'POST'])
@login_required
@admin_required
def view_logs():
    if request.args.get('file'):
        log = request.args.get('file')
    else:
        log = 'PanelPal.log'

    import glob
    files = []
    listing = glob.glob('*log*')
    for filename in listing:
        files.append(filename)


    result=[]
    with open(log) as f:
        for line in f:
            result.append(line.rstrip())

    return render_template('logs.html',log=result,files=files)

@admin.route('/admin/locked',methods=['GET', 'POST'])
@login_required
@admin_required
def view_locked(message=None):
    locked = get_all_locked(s)
    result = []
    for i in locked:
        row = dict(zip(i.keys(), i))
        result.append(row)
    table = ItemTableLocked(result, classes=['table', 'table-striped'])
    return render_template('locked.html',table=table,message=message)

@app.route("/admin/permissions", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_permissions_admin():
    users = get_users(s)
    result=OrderedDict()
    message=None
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
                status[username]=list()
                status[username].append(int(project_id))
            else:
                status[username].append(int(project_id))
        message = "Your changes have been made"

        print status
        #find changes
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
                            #this is OK it's checked and project
                            pass
                        else:
                            #not OK - it's been unchecked
                            print "username in but UNCHECKED"
                            remove_user_project_rel_no_id(s, username, project_id)
                    else:
                        if project_id in status[username]:
                            user_id=get_user_id_by_username(s,username)
                            add_user_project_rel(s,user_id,project_id)
                            print "NOW CHECKED"
                else:
                    if checked == "checked":
                        print "UNCHECKED"
                        remove_user_project_rel_no_id(s,username,project_id)

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
