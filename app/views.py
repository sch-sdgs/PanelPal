from flask import render_template, request, url_for, redirect
from flask_login import login_required, login_user, logout_user
from flask_table import LinkCol

from app.panel_pal import s, app, auto
from app.forms import Login
from mod_admin.queries import check_if_admin
from flask_login import LoginManager, current_user
from app.mod_admin.views import User
import traceback
import logging
from app.panel_pal import error_handler
# import sys
# from app.panel_pal import handle_exception

# sys.excepthook = handle_exception

# todo are these needed?
# class ItemTable(Table):
#     username = Col('Username')
#     id = Col('Id')
#     delete = LinkCol('Delete', 'delete_users', url_kwargs=dict(id='id'))
#
#
# class ItemTableUsers(Table):
#     username = Col('User')
#     admin = Col('Admin')
#     toggle_admin = LinkCol('Toggle Admin', 'toggle_admin', url_kwargs=dict(id='id'))
#
# class ItemTableLocked(Table):
#
#     name = Col('Panel')
#     username = Col('Locked By')
#     toggle_lock = LinkCol('Toggle Lock', 'toggle_locked', url_kwargs=dict(id='id'))

# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

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

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

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


@app.errorhandler(404)
def page_not_found(e):
    try:
        formatter = logging.Formatter('%(levelname)s|' + current_user.id + '|%(asctime)s|%(message)s')
    except AttributeError:
        formatter = logging.Formatter('%(levelname)s|anonymous|%(asctime)s|%(message)s')
    error_handler.setFormatter(formatter)
    app.logger.addHandler(error_handler)
    app.logger.error(traceback.format_exc())

    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    formatter = logging.Formatter('%(levelname)s|' + current_user.id + '|%(asctime)s|%(message)s')
    error_handler.setFormatter(formatter)
    app.logger.addHandler(error_handler)
    app.logger.error(traceback.format_exc())

    return render_template('500.html'), 500

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
    browser = request.user_agent.browser
    return render_template('home.html', panels=3, browser=browser)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/documentation')
def documentation():
    return auto.html()


class LinkColConditional(LinkCol):
    def td_contents(self, item, attr_list):
        if item["permission"] is True:
            return '<a href="{url}">{text}</a>'.format(
                url=self.url(item),
                text=self.td_format(self.text(item, attr_list)))
        else:
            return '-'