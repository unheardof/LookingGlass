from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_

import boto3
import json
import os.path
import sys
import datetime

from .internal_error import InternalError
from .tables import ChangeLog, Node, AdditionalNodeData, NetworkInterface, Edge, User, Workspace, AuthorizedWorkspaceUser, setup_tables

class DataGraph:

    def __init__(self, db='sqlite'):
        # Using SERIALIZABLE isolation ensures that any queried
        # information will not change in the midst of a transaction
        if db == 'sqlite':
            self.engine = create_engine('sqlite:////tmp/looking_glass.db', isolation_level='SERIALIZABLE')
        elif db == 'mysql':
            self.engine = create_engine(f'mysql+pymysql://{self._db_username()}:{self._db_password()}@db:3306/looking_glass', isolation_level='SERIALIZABLE')
        else:
            raise Exception(f"Unknown db type '{db}' encountered")

        self.Session = scoped_session(sessionmaker(bind=self.engine, autocommit=False))
        setup_tables(self.engine)

    def _db_username(self):
        return 'root'
        
    def _db_password(self):
        with open('/run/secrets/db-password', 'r') as pf:
            password = pf.read().strip()

        return password
        
    # A new transaction is implicitly started when a session is first used until the session.commit() method is called
    def create_session(self):
        return self.Session()

    def close_session(self):
        self.Session.remove()

    def load_user(self, user_id):
        return self.create_session().query(User).filter_by(id = user_id).first()

    def create_user(self, username, password):
        session = self.create_session()

        new_user = User(username, password)
        session.add(new_user)
        session.commit()

    def node_as_dict_with_additional_data(self, session, node):
        node_data = node.serializable_dict()
        additional_node_data_list = session.query(AdditionalNodeData).filter_by(node_id = node.id).all()
        node_network_interfaces = session.query(NetworkInterface).filter_by(node_id = node.id).all()

        for additional_node_data in additional_node_data_list:
            if additional_node_data.data_key == 'port_data':
                node_data[additional_node_data.data_key] = json.loads(
                    additional_node_data.data_value.replace("'", '"')
                )
            else:
                node_data[additional_node_data.data_key] = additional_node_data.data_value

        if len(node_network_interfaces) > 0:
            node_data['network_interfaces'] = [ i.as_dict() for i in node_network_interfaces ]            

        return node_data

    def create_workspace(self, user_id, workspace_name, default = False):
        session = self.create_session()

        if session.query(Workspace).filter_by(active = True, owning_user = user_id, name = workspace_name).first() is not None:
            return None

        new_workspace = Workspace(
            owning_user = user_id,
            name = workspace_name,
            default = default,
            active = True
        )

        session.add(new_workspace)
        session.commit()

        return new_workspace

    def delete_workspace(self, user_id, workspace_id):
        session = self.create_session()

        workspace = session.query(Workspace).filter_by(active = True, owning_user = user_id, id = workspace_id).first()

        if workspace is None:
            return False

        workspace.active = False
        session.add(workspace)
        session.commit()

        return True

    def grant_workspace_access(self, owning_user_id, workspace_id, authorized_user_id):
        session = self.create_session()

        # Can only share with users who exist
        if session.query(User).filter_by(id = authorized_user_id).first() is None:
            return False

        if session.query(Workspace).filter_by(active = True, owning_user = owning_user_id, id = workspace_id).first() is None:
            return False

        session.add(
            AuthorizedWorkspaceUser(
                workspace_id = workspace_id,
                authorized_user = authorized_user_id
            )
        )

        session.commit()

        return True

    def revoke_workspace_access(self, owning_user_id, workspace_id, unauthorized_user_id):
        session = self.create_session()

        user_authorization = session.query(AuthorizedWorkspaceUser).filter_by(workspace_id = workspace_id, authorized_user = unauthorized_user_id).first()

        if user_authorization is None:
            return False

        session.delete(user_authorization)
        session.commit()

        return True

    def can_user_access_workspace(self, session, username, workspace_id):
        access_allowed = False
        owned_workspace = session.query(Workspace).filter_by(active = True, owning_user = username, id = workspace_id).first()
        if owned_workspace is None:
            authorized_workspace = session.query(AuthorizedWorkspaceUser).filter_by(workspace_id = workspace_id, authorized_user = username).first()

            if authorized_workspace is not None:
                access_allowed = True
        else:
            access_allowed = True

        return access_allowed

    def workspaces_for_user(self, username):
        session = self.create_session()
        owned_workspaces = session.query(Workspace).filter_by(active = True, owning_user = username).all()

        authorizations = session.query(AuthorizedWorkspaceUser).filter_by(authorized_user = username).all()
        authorized_workspace_ids = [ a.workspace_id for a in authorizations ]
        authorized_workspaces = session.query(Workspace).filter(and_(Workspace.id.in_(authorized_workspace_ids), Workspace.active == True)).all()

        return owned_workspaces + authorized_workspaces

    def default_workspace_for_user(self, username):
        session = self.create_session()
        return session.query(Workspace).filter_by(owning_user = username, active = True, default = True).first()

    def changelog_row_for_update(self, session):
        new_version_number = ChangeLog.curr_version_number(session) + 1
        return ChangeLog(
            version_number = new_version_number,
            date_time = datetime.datetime.utcnow()
        )
    
    def current_graph_json(self, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return None

        nodes = session.query(Node).filter_by(active = True, workspace_id = workspace_id).all()
        current_version_number = ChangeLog.curr_version_number(session)

        nodes_by_id = {}
        for node in nodes:
            node_data = self.node_as_dict_with_additional_data(session, node)
            nodes_by_id[node.id] = node_data

        for edge in session.query(Edge).filter_by(active = True, workspace_id = workspace_id).all():
            if 'connections' in nodes_by_id[edge.source_node_id]:
                nodes_by_id[edge.source_node_id]['connections'].append(edge.serializable_dict())
            else:
                nodes_by_id[edge.source_node_id]['connections'] = [edge.serializable_dict()]

        return {
            'current_version_number': current_version_number,
            'nodes': list(nodes_by_id.values()) # Convert dict_values object to a list (https://markhneedham.com/blog/2017/03/19/python-3-typeerror-object-type-dict_values-not-json-serializable/)
        }

    def get_node_by_ip(self, node_ip, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return None

        node = session.query(Node).filter_by(active = True, ip = node_ip, workspace_id = workspace_id).first()

        if node:
            node = self.node_as_dict_with_additional_data(session, node)

        return node

    def upsert_node(self, node_dict, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return None

        # Lock the existing node record
        if 'id' in node_dict:
            for n in session.query(Node).filter_by(active = True, id = node_dict['id'], workspace_id = workspace_id).all():
                n.active = False
                session.add(n)

        # Split out any AdditionalNodeData and store that in that table accordingly
        node_obj_dict = {}
        additional_node_data = {}
        for key in node_dict:
            if key in Node.__table__.columns:
                node_obj_dict[key] = node_dict[key]
            else:
                additional_node_data[key] = node_dict[key]

        new_changelog_row = self.changelog_row_for_update(session)
        new_node = Node.from_dict(node_obj_dict, workspace_id)
        new_node.version_number = new_changelog_row.version_number

        session.add(new_changelog_row)
        session.flush() # make sure the new changelog row ID is fetched from the database
        
        session.add(new_node)
        session.flush() # make sure the new Node ID is fetched from the database
        
        for key in additional_node_data:
            session.add(
                AdditionalNodeData(
                    node_id = new_node.id,
                    data_key = key,
                    data_value = str(additional_node_data[key])
                )
            )

        session.commit()

    def upsert_edge(self, edge_data, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return None

        from_node_id = edge_data['from']
        to_node_id = edge_data['to']

        # Lock involved nodes and ensure that they exist
        source_node = session.query(Node).filter_by(active = True, id = from_node_id, workspace_id = workspace_id).first()
        destination_node = session.query(Node).filter_by(active = True, id = to_node_id, workspace_id = workspace_id).first()

        if not source_node or not destination_node:
            session.rollback()
            raise InternalError("Unable to create edge from node with ID of %s to node %s; at least one of these nodes does not exist" % (from_node_id, to_node_id))

        # Lock the existing edge records
        for e in session.query(Edge).filter_by(active = True, source_node_id = from_node_id, destination_node_id = to_node_id, workspace_id = workspace_id).all():
            e.active = False
            session.add(e)
        
        if 'previous_source_node' in edge_data and 'previous_destination_node' in edge_data:
            for e in session.query(Edge).filter_by(active = True, source_node_id = edge_data['previous_source_node'], destination_node_id = edge_data['previous_destination_node'], workspace_id = workspace_id).all():
                e.active = False
                session.add(e)

        new_changelog_row = self.changelog_row_for_update(session)

        label = '';
        if ('label' in edge_data):
            label = edge_data['label']

        new_edge = Edge(
            source_node_id = from_node_id,
            destination_node_id = to_node_id,
            workspace_id = workspace_id,
            version_number = new_changelog_row.version_number,
            label = label,
            active = True
        )

        session.add(new_edge)
        session.add(new_changelog_row)
        session.commit()

    def upsert_network_interface(self, arp_record, node_id, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            session.rollback()
            return None

        new_changelog_row = self.changelog_row_for_update(session)
        session.add(new_changelog_row)

        nodes = session.query(Node).filter_by(id = node_id, workspace_id = workspace_id, active = True).all()

        if len(nodes) != 1:
            session.rollback()
            raise InternalError('Expected to find exactly one active node with an ID of %s in workspace %s, but found %d' % (node_id, workspace_id, len(nodes)))

        node = nodes[0]
        if arp_record.mask is not None and node.subnet_mask != arp_record.mask:
            node.subnet_mask = arp_record.mask
            session.add(node)
        
        existing_interfaces = session.query(NetworkInterface).filter_by(node_id = node_id, workspace_id = workspace_id, mac_addr = arp_record.hw_address).all()
        
        if existing_interfaces is None or len(existing_interfaces) == 0:
            new_interface = NetworkInterface(
                node_id = node_id,
                workspace_id = workspace_id,
                name = arp_record.interface,
                mac_addr = arp_record.hw_address,
                hw_type = arp_record.hw_type,
                arp_flags = arp_record.flags
            )
            
            session.add(new_interface)
            
        elif len(existing_interfaces) > 1:
            raise InternalError("Expected at most one existing network interface entry for node %s in workspace %s with MAC address %s, but found %d" % (node_id, workspace_id, arp_record.hw_address, len(existing_interfaces)))
        else:
            existing_interface = existing_interfaces[0]
            
            if arp_record.interface is not None:
                existing_interface.name = arp_record.interface
                
            if arp_record.hw_address is not None:
                existing_interface.mac_addr = arp_record.hw_address
                    
            if arp_record.hw_type is not None:
                existing_interface.hw_type = arp_record.hw_type

            if arp_record.flags is not None:
                existing_interface.flags = arp_record.flags

            session.add(existing_interface)

        session.commit()
        
    def remove_node(self, node_id, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return None

        new_changelog_row = self.changelog_row_for_update(session)
        session.add(new_changelog_row)
        
        edges_from_node = session.query(Edge).filter_by(active = True, source_node_id = node_id, workspace_id = workspace_id).all()

        for edge in edges_from_node:
            edge.active = False

        session.add_all(edges_from_node)

        node = session.query(Node).filter_by(active = True, id = node_id, workspace_id = workspace_id).first()
        node.active = False
        session.add(node)

        session.commit()

    def remove_edge(self, from_node_id, to_node_id, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return None

        new_changelog_row = self.changelog_row_for_update(session)
        session.add(new_changelog_row)
        
        edge = session.query(Edge).filter_by(active = True, source_node_id = from_node_id, destination_node_id = to_node_id, workspace_id = workspace_id).first()
        edge.active = False
        session.add(edge)
        session.commit()

    def does_edge_exist(self, src_ip, dst_ip, username, workspace_id):
        session = self.create_session()

        if not self.can_user_access_workspace(session, username, workspace_id):
            return False

        src_node = session.query(Node).filter_by(active = True, ip = src_ip, workspace_id = workspace_id).first()
        dst_node = session.query(Node).filter_by(active = True, ip = dst_ip, workspace_id = workspace_id).first()

        if not (src_node and dst_node):
            return False

        edge = session.query(Edge).filter_by(active = True, source_node_id = src_node.id, destination_node_id = dst_node.id, workspace_id = workspace_id).first()

        return not edge is None
