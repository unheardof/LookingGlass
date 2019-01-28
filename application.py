# TODO: Send all traffic over HTTPS

from flask import Flask, request, render_template, send_from_directory, url_for, redirect, session, Response
from flask_login import current_user, login_required, LoginManager, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, validators

import argparse
import json
import os
import re
import uuid

from NmapQueryTool.nmap_query import ScanData
from lib.data_graph import DataGraph
from lib.tables import User

app = Flask(__name__)
application = app # Needed by Elastic Beanstalk / WSGI

app.config['SECRET_KEY'] = os.urandom(32)

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

data_graph = DataGraph()

# How to run locally (note: do not use this in production):
#
# FLASK_APP=application.py flask run --host=0.0.0.0
#

class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm', [validators.DataRequired()])
    displayname = StringField('DisplayName')
    submit = SubmitField('Submit')
    
@login_manager.user_loader
def load_user(username):
    return data_graph.load_user(username)
    
@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        if session.get('workspace_id') is None:
            session['workspace_id'] = data_graph.default_workspace_for_user(current_user.get_username()).id

        session['workspaces'] = [ { 'name': w.name, 'id': w.id } for w in data_graph.workspaces_for_user(current_user.get_username()) ]
        
        return render_template('infrastructure_graph.html')
    else:
        return render_template('login.html', form=LoginForm())

# Reference: https://flask-login.readthedoces.io/en/latest
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    error = None
    
    if form.validate_on_submit():
        user = data_graph.load_user(form.username.data)

        if not user is None:
            login_user(user, remember=True)

            # TODO: Allow switching between workspaces
            available_workspaces = data_graph.workspaces_for_user(current_user.get_username())
            if available_workspaces is None or len(available_workspaces) == 0:
                new_workspace = data_graph.create_workspace(current_user.get_username(), 'DEFAULT', True)
                session['workspace_id'] = new_workspace.id
            else:
                session['workspace_id'] = available_workspaces[0].id

            print('Logged in successfully')
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
            
    return render_template('login.html', form=form, error=error)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session['workspace_id'] = None
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    error = None

    if request.method == 'POST' and form.validate():
        user = data_graph.load_user(form.username.data)

        if user is None:
            if form.password.data != form.confirm.data:
                error = 'Passwords do not match'
            else:
                data_graph.create_user(form.username.data.encode('utf-8'), form.password.data.encode('utf-8'))
                
                print('User %s has been registered' % form.username.data)
                return redirect(url_for('login'))
        else:
            error = 'User with username %s already exists' % form.username.data
    
    return render_template('register_user.html', form=form, error=error)

@app.route('/create_workspace', methods=['POST'])
@login_required
def create_workspace():
    success = data_graph.create_workspace(request.json['user_id'], request.json['data']['workspace_name'])

    if not success:
        response = Response('Unable to create workspace %s' % workspace_name)
        response.status_code = 409 # Conflict error code
        return response
    else:
        response = Response()
        response.status_code = 200
        return response

@app.route('/graph_data', methods=['GET'])
def get_graph_data():
    if current_user.is_authenticated:
        graph_json = data_graph.current_graph_json(request.args.get('user_id'), request.args.get('workspace_id'))

        if graph_json is None:
            return Response('User not allowed to access the requested workspace', status=403)
        else:
            return json.dumps(graph_json)
    else:
        return redirect(url_for('login'))

@app.route('/upsert_node', methods=['POST'])
@login_required
def upsert_node():
    data_graph.upsert_node(request.json['data'], request.json['user_id'], request.json['workspace_id'])
    return 'ok'

@app.route('/add_edge', methods=['POST'])
@login_required
def add_edge():
    data_graph.add_edge(request.json['data'], request.json['user_id'], request.json['workspace_id'])
    return 'ok'

@app.route('/remove_node', methods=['POST'])
@login_required
def remove_node():
    data_graph.remove_node(request.json['data'], request.json['user_id'], request.json['workspace_id'])
    return 'ok'

@app.route('/remove_edge', methods=['POST'])
@login_required
def remove_edge():
    edge_data = request.json['data']
    data_graph.remove_edge(edge_data['from'], edge_data['to'], request.json['user_id'], request.json['workspace_id'])
    return 'ok'

@app.route('/upload_nmap_data', methods=['POST'])
@login_required
def upload_nmap_data():
    nmap_data = request.json['data']
    username = request.json['user_id']
    session['workspace_id'] = request.json['workspace_id']
    
    data = ScanData.create_from_nmap_data(nmap_data.encode('utf-8'))
    
    for host in data.host_data_list():
        node = data_graph.get_node_by_ip(host.ip, username, session['workspace_id'])

        node_updated = False
        
        if node == None:
            node_updated = True
            node = { 'id': str(uuid.uuid4()) }

        host_dict = host.as_dict()

        if 'os_list' in host_dict:
            windows_os_pattern = re.compile('.*[Ww]indows.*')
            linux_os_pattern = re.compile('.*[Ll]inux.*')
            
            if any([ windows_os_pattern.match(x) for x in host_dict['os_list'] ]):
                node['group'] = 'windows_host'
            elif any([ linux_os_pattern.match(x) for x in host_dict['os_list'] ]):
                node['group'] = 'linux_host'
        
        for key in host_dict:
            if not key in node:
                node[key] = host_dict[key]
                node_updated = True
            elif node[key] != host_dict[key]:
                print('WARN: Node with IP %s currently has %s data (%s) which does not match the data found by the nmap scan (%s); ignoring the new data' % (host.ip, key, str(node[key]), str(host_dict[key])))
            else:
                print("Node with IP of %s already has the same %s data; no action necessary" % (host.ip, key))

        if node_updated:
            data_graph.upsert_node(node, username, session['workspace_id'])
        
    return 'ok'

if __name__ == '__main__':
    # TODO: pip install pyopenssl
    app.run(ssl_context='adhoc')
