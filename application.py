from flask import Flask, request, render_template, send_from_directory

import argparse
import boto3
import os.path
import sys

# TODO: Implement graph version tracking on a per node basis (which encompasses the edges from that node) rather than on the graph as whole
# TODO: Write data to a better / more persistent store (i.e. a database)

S3_BUCKET = 'looking-glass-data'
FILENAME = 'graph_data.json'
DATA_FILE = '/tmp/' + FILENAME

app = Flask(__name__)
application = app # Needed by Elastic Beanstalk / WSGI

# TODO: Get this figured out (See http://flask.pocoo.org/snippets/133/)
# parser = argparse.ArgumentParser(description='Start the Looking Glass application')
# parser.add_argument('--local', action='store_true', help='If provided, the script will use the local filesystem for persistence (instead of S3)')
# args = parser.parse_args()
    
#app.config['local_mode'] = args.local
#app.run()

app.config['local_mode'] = True

# How to run locally (note: do not use this in production): FLASK_APP=application.py flask run --host=0.0.0.0

@app.route('/', methods=['GET'])
def index():
    return render_template('infrastructure_graph.html')

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/graph_data', methods=['GET'])
def get_graph_data():
    data = None

    if app.config['local_mode']:
        if os.path.isfile(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = f.read()
    else:
        s3 = boto3.client('s3')

        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=FILENAME)
            data = obj['Body'].read().decode('utf-8')
        except:
            print('No file with key %s in the %s bucket' % (FILENAME, S3_BUCKET)) 
            
    if (data == None or data.strip() == ''):
        data = '{}' # Ensure that we always return valid JSON
        
    return data

# TODO: Integrate MongoDB as the persistence rather than a static file
# => could create a free DB to use
# => https://www.mongodb.com/mongodb-4.0?jmp=homepagenull
# => https://docs.mongodb.com/tutorials/install-mongodb-on-windows/
# TODO: Only send the update rather than the entire graph state
# TODO: Update the requirements.txt file
@app.route('/update', methods=['POST'])
def update():
    print("Received %s" % request.json)

    if app.config['local_mode']:
        with open(DATA_FILE, 'w') as f:
            if isinstance(request.data, bytes):
                f.write(request.data.decode())
            else:
                f.write(request.data)
    else:
        s3 = boto3.client('s3')
        s3.put_object(Body=request.data, Bucket=S3_BUCKET, Key=FILENAME)
        

    return 'ok'

@app.route('/add_nmap_results', methods=['POST'])
def add_nmap_results():
    print("add_nmap_results: received %s" % request.json)


# TODO: Get this to actually work or remove it
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the Looking Glass application')
    parser.add_argument('--local', action='store_true', help='If provided, the script will use the local filesystem for persistence (instead of S3)')
    args = parser.parse_args()
    
    app.config['local_mode'] = args.local
    app.run()
