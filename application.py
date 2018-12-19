from flask import Flask, request, render_template, send_from_directory

import argparse
import re
import uuid

from NmapQueryTool.nmap_query import ScanData

from lib.data_graph import DataGraph

app = Flask(__name__)
application = app # Needed by Elastic Beanstalk / WSGI

# TODO: Use or remove
app.config['local_mode'] = True

data_graph = DataGraph()

# How to run locally (note: do not use this in production):
#
# FLASK_APP=application.py flask run --host=0.0.0.0
#

@app.route('/', methods=['GET'])
def index():
    return render_template('infrastructure_graph.html')

@app.route('/graph_data', methods=['GET'])
def get_graph_data():
    return data_graph.current_graph_json()

@app.route('/upsert_node', methods=['POST'])
def upsert_node():
    print("Received call to upsert_node API with: %s" % request.json)
    data_graph.upsert_node(request.json)
    return 'ok'

@app.route('/add_edge', methods=['POST'])
def add_edge():
    print("Received call to add_edge API with: %s" % request.json)
    data_graph.add_edge(request.json)
    return 'ok'

@app.route('/remove_node', methods=['POST'])
def remove_node():
    print("Received call to remove_node API with: %s" % request.json)
    data_graph.remove_node(request.json)
    return 'ok'

@app.route('/remove_edge', methods=['POST'])
def remove_edge():
    print("Received call to remove_edge API with: %s" % request.json)
    data_graph.remove_edge(request.json['from'], request.json['to'])
    return 'ok'

@app.route('/upload_nmap_data', methods=['POST'])
def upload_nmap_data():
    print("upload_nmap_data: received %s" % request.json)

    data = ScanData.create_from_nmap_data(request.json)
    
    for host in data.host_data_list():
        node = data_graph.get_node_by_ip(host.ip)

        node_updated = False
        
        if node == None:
            node_updated = True
            node = { 'id': str(uuid.uuid4()) }

        host_dict = host.as_dict()

        if 'os_list' in host_dict:
            if re.match('.*[Ww]indows.*', host_dict['os_list']):
                node['group'] = 'windows_host'
            elif re.match('.*[Ll]inux.*', host_dict['os_list']):
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
            data_graph.upsert_node(node)
        
    return 'ok'

# TODO: Get this to actually work or remove it
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the Looking Glass application')
    parser.add_argument('--local', action='store_true', help='If provided, the script will use the local filesystem for persistence (instead of S3)')
    args = parser.parse_args()
    
    app.config['local_mode'] = args.local
    app.run()
