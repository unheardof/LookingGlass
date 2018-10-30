from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import boto3
import os.path
import sys
import json

from .tables import ChangeLog, Node, Edge, setup_tables

class DataGraph:
    # TODO: Get rid of these
    S3_BUCKET = 'looking-glass-data'
    FILENAME = 'graph_data.json'
    DATA_FILE = '/tmp/' + FILENAME

    def __init__(self):
        # TODO: Change back
        #engine = create_engine('sqlite:///looking_glass.db')
        self.engine = create_engine('sqlite:///:memory:')
        setup_tables(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.nodes_by_id = {}

    def current_graph_json(self, local_mode=True):
        # TODO: Pull out the list of values and convert to string
        print('Graph:\n\n{ "nodes": %s }' %( str(self.nodes_by_id.values()) ))

        # TODO: decode all strings within each node
        #return '{ "nodes": %s }' %( str(self.nodes_by_id.values()) )
        return '{ "nodes": %s }' %( json.dumps(self.nodes_by_id.values()) )
        
        # TODO: Persist nodes_by_id to file (and then DB) and then cleanup
        #data = None

        # if local_mode:
        #     if os.path.isfile(DataGraph.DATA_FILE):
        #         with open(DataGraph.DATA_FILE, 'r') as f:
        #             data = f.read()
        # else:
        #     s3 = boto3.client('s3')

        #     try:
        #         obj = s3.get_object(Bucket=DataGraph.S3_BUCKET, Key=DataGraph.FILENAME)
        #         data = obj['Body'].read().decode('utf-8')
        #     except:
        #         print('No file with key %s in the %s bucket' % (DataGraph.FILENAME, DataGraph.S3_BUCKET)) 
            
        # if (data == None or data.strip() == ''):
        #     data = '{}' # Ensure that we always return valid JSON
        
        # return data

    def upsert_node(self, node):
        print("Node: %s" % (node))
        
        if node['id'] in self.nodes_by_id:
            print("Updating node with ID %s" % node['id'])
        else:
            print("Creating new node with ID %s" % node['id'])

        self.nodes_by_id[node['id']] = node
            
    def add_edge(self, edge):
        print("Edge: %s" % (edge))

        from_node_id = edge['from']
        if not from_node_id in self.nodes_by_id:
            raise "Unable to create edge; from node with ID of %s does not exist" % from_node_id

        if 'connections' in self.nodes_by_id[from_node_id]:
            self.nodes_by_id[from_node_id]['connections'].append(edge['to'])
        else:
            self.nodes_by_id[from_node_id]['connections'] = [edge['to']]

    def remove_node(self, node_id):
        print("Removing Node: %s" % (node_id))
        del self.nodes_by_id[node_id]

    def remove_edge(self, from_node_id, to_node_id):
        print("Removing edge from: %s to %s" % (from_node_id, to_node_id))
        if from_node_id in self.nodes_by_id:
            self.nodes_by_id[from_node_id]['connections'].remove(to_node_id)
        else:
            print("Edge from %s to %s not found; must have already been removed" % (from_node_id, to_node_id))

    # TODO: add functions for merging additional data (NMAP, PCAP, ARP, etc.) into the graph data
