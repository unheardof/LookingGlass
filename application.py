from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, url_for, redirect, session, Response
from flask_login import current_user, login_required, LoginManager, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from scapy.utils import rdpcap
from wtforms import StringField, PasswordField, SubmitField, validators

import argparse
import io
import json
import logging
import os
import re
import threading
import uuid

from NmapQueryTool.lib.scan_data import ScanData
from lib.data_graph import DataGraph
from lib.tables import User
from lib.arp import parse_arp_data

BASE_UPLOAD_FOLDER = './user_files'

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

# Static helper functions

def defaultWorkspaceName():
    return current_user.get_username() + "'s workspace"

def pcap_filename(username):
    # Use timestamp to keep a record of when the PCAP was uploaded, but add a UUID in case the same user submits
    # multiple PCAP files in the same second (which is unlikely, but technically possible)
    return "%s-%s-%s.pcap" % (username, datetime.utcnow().strftime('%Y%m%dT%H%M%S'), str(uuid.uuid4()))

def create_node(node_ip):
    return {
        'id': str(uuid.uuid4()),
        'ip': node_ip
    }

# API Implementations

@login_manager.user_loader
def load_user(username):
    return data_graph.load_user(username)

@app.teardown_request
def remove_session(ex=None):
    data_graph.close_session()

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

        if not user is None and user.validate_password(form.password.data.encode('utf-8')):
            login_user(user, remember=True)

            available_workspaces = data_graph.workspaces_for_user(current_user.get_username())
            if available_workspaces is None or len(available_workspaces) == 0:
                new_workspace = data_graph.create_workspace(current_user.get_username(), defaultWorkspaceName(), True)
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

    if request.method == 'POST':
        if form.validate():
            user = data_graph.load_user(form.username.data)

            if user is None:
                if form.password.data != form.confirm.data:
                    error = 'Passwords do not match'
                else:
                    data_graph.create_user(form.username.data, form.password.data.encode('utf-8'))

                    print('User %s has been registered' % form.username.data)
                    return redirect(url_for('login'))
            else:
                error = 'User with username %s already exists' % form.username.data
        else:
            error = 'Form validation failed; passwords must match'

    return render_template('register_user.html', form=form, error=error)

@app.route('/create_workspace', methods=['POST'])
@login_required
def create_workspace():
    workspace_name = request.json['workspace_name']
    success = data_graph.create_workspace(request.headers.get('user_id'), workspace_name)

    if success:
        response = Response()
        response.status_code = 200
        return response
    else:
        response = Response('Unable to create workspace %s' % workspace_name)
        response.status_code = 409 # Conflict error code
        return response

@app.route('/delete_workspace', methods=['POST'])
@login_required
def delete_workspace():
    workspace_id = request.headers.get('workspace_id')
    success = data_graph.delete_workspace(request.headers.get('user_id'), workspace_id)

    if success:
        response = Response()
        response.status_code = 200
        return response
    else:
        response = Response('Unable to delete workspace (ID: %s)' % workspace_id)
        response.status_code = 400
        return response

@app.route('/share_workspace', methods=['POST'])
@login_required
def share_workspace():
    workspace_id = request.headers.get('workspace_id')
    success = data_graph.grant_workspace_access(request.headers.get('user_id'), workspace_id, request.json['authorized_user'])

    if success:
        response = Response()
        response.status_code = 200
        return response
    else:
        response = Response('Unable to share workspace (ID: %s)' % workspace_id)
        response.status_code = 403 # Forbidden
        return response

@app.route('/unshare_workspace', methods=['POST'])
@login_required
def unshare_workspace():
    workspace_id = request.headers.get('workspace_id')
    success = data_graph.revoke_workspace_access(request.headers.get('user_id'), workspace_id, request.json['unauthorized_user'])

    if success:
        response = Response()
        response.status_code = 200
        return response
    else:
        response = Response('Unable to revoke permissions for the %s user for workspace with ID: %s' % (request.json['unauthorized_user'], workspace_id))
        response.status_code = 403 # Forbidden
        return response

@app.route('/workspaces', methods=['GET'])
@login_required
def get_workspaces_for_user():
    session['workspaces'] = [ { 'name': w.name, 'id': w.id } for w in data_graph.workspaces_for_user(current_user.get_username()) ]
    return Response(json.dumps(session['workspaces']))

@app.route('/graph_data', methods=['GET'])
def get_graph_data():
    try:
        if current_user.is_authenticated:
            graph_json = data_graph.current_graph_json(request.args.get('user_id'), request.args.get('workspace_id'))

            if graph_json is None:
                return Response('User not allowed to access the requested workspace', status=403)
            else:
                return json.dumps(graph_json)
        else:
            return redirect(url_for('login'))
    except Exception as err:
        print("[ERROR] %s" % err)
        return Response(str(err), status=400)

@app.route('/upsert_node', methods=['POST'])
@login_required
def upsert_node():
    data_graph.upsert_node(request.json, request.headers.get('user_id'), request.headers.get('workspace_id'))
    return 'ok'

@app.route('/add_edge', methods=['POST'])
@login_required
def add_edge():
    data_graph.add_edge(request.json, request.headers.get('user_id'), request.headers.get('workspace_id'))
    return 'ok'

@app.route('/remove_node', methods=['POST'])
@login_required
def remove_node():
    data_graph.remove_node(request.json, request.headers.get('user_id'), request.headers.get('workspace_id'))
    return 'ok'

@app.route('/remove_edge', methods=['POST'])
@login_required
def remove_edge():
    edge_data = request.json
    data_graph.remove_edge(edge_data['from'], edge_data['to'], request.headers.get('user_id'), request.headers.get('workspace_id'))
    return 'ok'

def merge_new_node_data(node, new_data):
    node_updated = False

    for key in new_data:
        if not key in node:
            node[key] = new_data[key]
            node_updated = True
        elif node[key] != new_data[key]:
            # TODO: Create list of values for key instead of ignoring the new data
            print("WARN: Node with IP %s currently has data '%s' for key '%s', which does not match the new data found, '%s'; ignoring the new data" % (node['ip'], str(node[key]), key, str(new_data[key])))
        else:
            print("Node with IP of %s already has the same data for key '%s'; no action necessary" % (node['ip'], key))

    return { 'node_updated': node_updated, 'node': node }

@app.route('/upload_nmap_data', methods=['POST'])
@login_required
def upload_nmap_data():
    nmap_data = request.json
    username = request.headers.get('user_id')
    session['workspace_id'] = request.headers.get('workspace_id')
    data = ScanData.create_from_nmap_data(io.StringIO(nmap_data))

    for host in data.host_data_list():
        node = data_graph.get_node_by_ip(host.ip, username, session['workspace_id'])

        node_updated = False

        if node == None:
            node_updated = True
            node = create_node(host.ip)

        host_dict = host.as_dict()

        if 'os_list' in host_dict:
            windows_os_pattern = re.compile('.*[Ww]indows.*')
            linux_os_pattern = re.compile('.*[Ll]inux.*')

            if any([ windows_os_pattern.match(x) for x in host_dict['os_list'] ]):
                node['group'] = 'windows_host'
            elif any([ linux_os_pattern.match(x) for x in host_dict['os_list'] ]):
                node['group'] = 'linux_host'

        results = merge_new_node_data(node, host_dict)
        node_updated |= results['node_updated']
        node = results['node']

        if node_updated:
            data_graph.upsert_node(node, username, session['workspace_id'])

    return 'ok'

@app.route('/upload_arp_data', methods=['POST'])
@login_required
def upload_arp_data():
    username = request.headers.get('user_id')
    session['workspace_id'] = request.headers.get('workspace_id')
    arp_records = parse_arp_data(request.json)

    for arp_record in arp_records:
        node = data_graph.get_node_by_ip(arp_record.address, username, session['workspace_id'])

        node_updated = False

        if node == None:
            node_updated = True
            node = create_node(arp_record.address)

        results = merge_new_node_data(node, arp_record.as_dict())
        node_updated |= results['node_updated']
        node = results['node']

        if node_updated:
            data_graph.upsert_node(node, username, session['workspace_id'])

    return 'ok'

# Reference: http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
@app.route('/upload_pcap_data', methods=['POST'])
@login_required
def upload_pcap_data():
    username = request.headers.get('user_id')
    session['workspace_id'] = request.headers.get('workspace_id')

    directory_path = os.path.join(BASE_UPLOAD_FOLDER, username, 'pcaps')
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    file_path = os.path.join(directory_path, pcap_filename(username))

    with open(file_path, 'w') as f:
        f.write(request.data)

    # TODO: Implement functionality for parsing the PCAP file and pulling information into the graph

    return 'ok'

# Expected data format:
#
# 192.168.0.1 172.3.4.35
# 10.3.4.5 9.2.34.5
#
@app.route('/upload_net_flow_data', methods=['POST'])
@login_required
def upload_net_flow():
    username = request.headers.get('user_id')
    session['workspace_id'] = request.headers.get('workspace_id')
    error = None

    for line in request.data.decode('utf-8').replace('\\n', '\n').split("\n"):
        stripped_line = line.strip().replace('\"', '').replace('\'', '')

        if len(stripped_line) == 0:
            continue

        addresses = stripped_line.split(' ')

        if len(addresses) != 2:
            response = Response("Provided net flow data did not have the expected format; expect each line to be of the form '<Source IP Address> <Destination IP Address>'")
            response.status_code = 400 # Bad request
            return response

        src_ip = addresses[0].strip()
        dst_ip = addresses[1].strip()

        src_node = data_graph.get_node_by_ip(src_ip, username, session['workspace_id'])
        dst_node = data_graph.get_node_by_ip(dst_ip, username, session['workspace_id'])

        new_edge = False
        if src_node == None:
            src_node = create_node(src_ip)
            data_graph.upsert_node(src_node, username, session['workspace_id'])
            new_edge = True

        if dst_node == None:
            dst_node = create_node(dst_ip)
            data_graph.upsert_node(dst_node, username, session['workspace_id'])
            new_edge = True

        if new_edge or not data_graph.does_edge_exist(src_ip, dst_ip, username, session['workspace_id']):
            edge = { 'from': src_node['id'], 'to': dst_node['id'] }
            data_graph.add_edge(edge, username, session['workspace_id'])

    return 'ok'

# TODO: Also add support for importing SiLK NetFlow data (can convert PCAP's using the rwp2yaf2silk tool

if __name__ == '__main__':
    verbose = False
    parser = argparse.ArgumentParser(description='Development mode command line options')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if not args.verbose:
        # Silence Flask server logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        app.logger.disabled = True

    # TODO: Enable HTTPS (need to generate a SSL certificate during setup in order for this to actually work)
    #app.run(ssl_context='adhoc', threaded=True)
    app.run(threaded=True)
