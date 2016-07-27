from app import app
from models import *
from panel_pal.db_commands import *
import sqlite3
from flask import Flask, render_template, request, flash
from forms import UserForm
from flask_bootstrap import Bootstrap

app.secret_key = 'development key'

@app.route('/')
def index():
    return render_template('home.html',panels=3)

@app.route('/panels')
def view_panels():
    conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
    panels = str(get_panel(panel='HSPRecessive',team_id=6,conn=conn_panelpal))
    return render_template('panels.html',panels=panels)

@app.route('/users')
def view_users():
    conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
    users = str(get_users(conn_panelpal))
    return render_template('users.html',users=users)

@app.route('/users/add', methods=['GET', 'POST'])
def add_users():
    form = UserForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('users_add.html', form=form)
        else:
            conn_panelpal = sqlite3.connect('../panel_pal/resources/panel_pal.db')
            print form.data["name"]
            id = add_user(form.data["name"], conn_panelpal)
            return view_users()

    elif request.method == 'GET':
        return render_template('users_add.html', form=form)
