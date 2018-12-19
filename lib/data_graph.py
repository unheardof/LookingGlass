from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import boto3
import os.path
import sys
import json
import datetime

from .tables import ChangeLog, Node, AdditionalNodeData, Edge, setup_tables

class DataGraph:

    def __init__(self):
        # Using SERIALIZABLE isolation ensures that any queried
        # information will not change in the midst of a transaction
        self.engine = create_engine('sqlite:///looking_glass.db', isolation_level='SERIALIZABLE')
        
        setup_tables(self.engine)

    # A new transaction is implicitly started when a session is first used until the session.commit() method is called
    def create_session(self):
        Session = sessionmaker(bind=self.engine, autocommit=False)
        return Session()

    def node_as_dict_with_additional_data(self, session, node):
        additional_node_data_list = session.query(AdditionalNodeData).filter_by(node_id = node.id).all()
        node_data = node.serializable_dict()

        for additional_node_data in additional_node_data_list:
            node_data[additional_node_data.data_key] = additional_node_data.data_value

        return node_data

    def current_graph_json(self):
        session = self.create_session()
        nodes = session.query(Node).filter_by(active = True).all()
        current_version_number = ChangeLog.curr_version_number(session)

        nodes_by_id = {}
        for node in nodes:
            node_data = self.node_as_dict_with_additional_data(session, node)
            nodes_by_id[node.id] = node_data
        
        for edge in session.query(Edge).filter_by(active = True).all():
            if 'connections' in nodes_by_id[edge.source_node_id]:
                nodes_by_id[edge.source_node_id]['connections'].append(edge.destination_node_id)
            else:
                nodes_by_id[edge.source_node_id]['connections'] = [edge.destination_node_id]

        graph = {
            'current_version_number': current_version_number,
            'nodes': nodes_by_id.values()
        }
            
        return json.dumps(graph)

    def get_node_by_ip(self, node_ip):
        session = self.create_session()
        node = session.query(Node).filter_by(ip = node_ip, active = True).first()

        if node:
            node = self.node_as_dict_with_additional_data(session, node)

        return node
    
    def upsert_node(self, node_dict):
        session = self.create_session()

        # Lock the existing node record
        if 'id' in node_dict:
            for n in session.query(Node).filter_by(id = node_dict['id'], active = True).all():
                n.active = False
                session.add(n)

            session.query(Node).filter_by(id = node_dict['id'], active = True).first()

        # Split out any AdditionalNodeData and store that in that table accordingly
        node_obj_dict = {}
        additional_node_data = {}
        for key in node_dict:
            if key in Node.__table__.columns:
                node_obj_dict[key] = node_dict[key]
            else:
                additional_node_data[key] = node_dict[key]

        current_version_number = ChangeLog.curr_version_number(session)
        new_version_number = current_version_number + 1

        new_changelog_row = ChangeLog(
            version_number = new_version_number,
            date_time = datetime.datetime.utcnow()
        )

        new_node = Node.from_dict(node_obj_dict)
        new_node.version_number = new_version_number

        session.add(new_node)
        session.add(new_changelog_row)
        
        for key in additional_node_data:
            session.add(
                AdditionalNodeData(
                    node_id = new_node.id,
                    data_key = key,
                    data_value = str(additional_node_data[key])
                )
            )

        session.commit()

    def add_edge(self, edge):
        session = self.create_session()
        current_version_number = ChangeLog.curr_version_number(session)

        from_node_id = edge['from']
        source_node = session.query(Node).filter_by(id = from_node_id, active = True).first()
        
        if not source_node:
            session.rollback()
            raise "Unable to create edge; from node with ID of %s does not exist" % from_node_id

        new_version_number = current_version_number + 1

        new_changelog_row = ChangeLog(
            version_number = new_version_number,
            date_time = datetime.datetime.utcnow()
        )

        new_edge = Edge(
            source_node_id = edge['from'],
            destination_node_id = edge['to'],
            version_number = new_version_number,
            active = True
            )
        
        session.add(new_edge)
        session.add(new_changelog_row)
        session.commit()

    def remove_node(self, node_id):
        session = self.create_session()
        edges_from_node = session.query(Edge).filter_by(source_node_id = node_id, active = True).all()
        
        for edge in edges_from_node:
            edge.active = False

        node = session.query(Node).filter_by(id = node_id).first()
        node.active = False

        session.add_all(edges_from_node)
        session.add(node)
        session.commit()

    def remove_edge(self, from_node_id, to_node_id):
        session = self.create_session()
        edge = session.query(Edge).filter_by(source_node_id = from_node_id, active = True).first()
        edge.active = False
        session.add(edge)
        session.commit()
        
    # TODO: add functions for merging additional data (NMAP, PCAP, ARP, etc.) into the graph data
