from flask import Flask, request, render_template, send_from_directory
import boto3
import os.path

# TODO: Implement graph version tracking on a per node basis (which encompasses the edges from that node) rather than on the graph as whole
# TODO: Write data to a better / more persistent store (i.e. a database)

S3_BUCKET = 'looking-glass-data'
FILENAME = 'graph_data.json'
DATA_FILE = '/tmp/' + FILENAME

# TODO: Change this to a command-line option (which defaults to False)
# Change this to True to run this locally
LOCAL_MODE = True

app = Flask(__name__)
application = app # Needed by Elastic Beanstalk / WSGI

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

    if LOCAL_MODE:
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

@app.route('/update', methods=['POST'])
def update():
    print("Received %s" % request.json)

    if LOCAL_MODE:
        with open(DATA_FILE, 'w') as f:
            if isinstance(request.data, bytes):
                f.write(request.data.decode())
            else:
                f.write(request.data)
    else:
        s3 = boto3.client('s3')
        s3.put_object(Body=request.data, Bucket=S3_BUCKET, Key=FILENAME)
        

    return 'ok'
