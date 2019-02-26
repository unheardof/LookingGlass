import datetime

from flask_login import UserMixin

import bcrypt
import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, Float, DateTime, String, Boolean
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column(String(30), primary_key = True)
    password = Column(String(300), nullable=False)

    def __init__(self, username, password):
        self.id = username
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())

    def validate_password(self, password):
        return bcrypt.checkpw(password, self.password)

    def get_id(self):
        return self.id

    def get_username(self):
        return self.id

class Workspace(Base):
    __tablename__ = 'workspaces'

    id = Column(Integer, primary_key = True)
    owning_user = Column(String, ForeignKey("users.id"), nullable = False, index = True)
    name = Column(String, nullable = False, index = True)
    default = Column(Boolean, nullable = True, index = True)
    active = Column(Boolean)

class AuthorizedWorkspaceUser(Base):
    __tablename__ = 'authorized_workspace_users'

    workspace_id = Column(Integer, ForeignKey("workspaces.id"), primary_key = True)
    authorized_user = Column(Integer, ForeignKey("users.id"), primary_key = True)

class ChangeLog(Base):
    __tablename__ = 'change_log'

    # Authoritative graph version number (i.e. logical time)
    version_number = Column(Integer, primary_key = True)

    # Index on date_time to allow efficient data-based queries
    date_time = Column(DateTime, default=datetime.datetime.utcnow(), index = True)

    @staticmethod
    def curr_version_number(session):
        return session.query(ChangeLog).order_by(ChangeLog.version_number.desc()).first().version_number

# Used for associating additional data, such as open ports, operating system version, etc.
# with a given node
class AdditionalNodeData(Base):
    __tablename__ = 'additional_node_data'

    id = Column(Integer, primary_key = True)
    node_id = Column(String, ForeignKey("nodes.id"))
    data_key = Column(String)
    data_value = Column(String)

class Node(Base):
    __tablename__ = 'nodes'

    # Composite key on node (ID, version number) to allow for keeping a historical record of changes to the graph;
    # this will allow for undo-redo functionality as well as point-in-time playbacks / lookbacks using the change_log table
    # to get the date-time when the change was made
    id = Column(String, primary_key = True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), primary_key = True)
    version_number = Column(Integer, ForeignKey("change_log.version_number"), primary_key = True)
    hostname = Column(String)
    ip = Column(String)
    x_coordinate = Column(Float)
    y_coordinate = Column(Float)
    group = Column(String, default = 'other')
    active = Column(Boolean)

    def serializable_dict(self):
        d = self.__dict__
        del d['_sa_instance_state']

        return d

    @staticmethod
    def from_dict(node, workspace_id):
        return Node(
            id = node.get('id'),
            workspace_id = workspace_id,
            version_number = node.get('version_number'),
            hostname = node.get('hostname'),
            ip = node.get('ip'),
            x_coordinate = node.get('x'),
            y_coordinate = node.get('y'),
            group = node.get('group'),
            active = True
        )

class Edge(Base):
    __tablename__ = 'edges'

    source_node_id = Column(Integer, ForeignKey("nodes.id"), primary_key = True)
    destination_node_id = Column(Integer, ForeignKey("nodes.id"), primary_key = True)
    version_number = Column(Integer, ForeignKey("change_log.version_number"), primary_key = True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), primary_key = True)
    active = Column(Boolean)

def setup_tables(engine):
    # TODO: Implement support for performing database migration / schema change if needed
    
    if not engine.dialect.has_table(engine, 'change_log'):
        Base.metadata.create_all(engine)

    # Initialize changelog table
    Session = sessionmaker(bind=engine, autocommit=False)
    session = Session()
    if session.query(ChangeLog).count() == 0:
        first_changelog_row = ChangeLog(
            version_number = 0,
            date_time = datetime.datetime.utcnow()
        )

        session.add(first_changelog_row)

    session.commit()
        
