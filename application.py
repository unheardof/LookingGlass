from flask import Flask, request, render_template, send_from_directory

import argparse

from lib.data_graph import DataGraph

app = Flask(__name__)
application = app # Needed by Elastic Beanstalk / WSGI

# TODO: Update the requirements.txt file to include SQL Alchemy
# TODO: Get this figured out (See http://flask.pocoo.org/snippets/133/)
# parser = argparse.ArgumentParser(description='Start the Looking Glass application')
# parser.add_argument('--local', action='store_true', help='If provided, the script will use the local filesystem for persistence (instead of S3)')
# args = parser.parse_args()
    
#app.config['local_mode'] = args.local
#app.run()

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
    return data_graph.current_graph_json(app.config['local_mode'])

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

@app.route('/add_nmap_results', methods=['POST'])
def add_nmap_results():
    # TODO: Implement
    print("add_nmap_results: received %s" % request.json)

# TODO: Get this to actually work or remove it
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the Looking Glass application')
    parser.add_argument('--local', action='store_true', help='If provided, the script will use the local filesystem for persistence (instead of S3)')
    args = parser.parse_args()
    
    app.config['local_mode'] = args.local
    app.run()
