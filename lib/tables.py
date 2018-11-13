import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, Float, DateTime, String, Boolean
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ChangeLog(Base):
    __tablename__ = 'change_log'

    # Authoritative graph version number (i.e. logical time)
    version_number = Column(Integer, primary_key = True)

    # Index on date_time to allow efficient data-based queries
    date_time = Column(DateTime, default=datetime.datetime.utcnow(), index = True)

    @staticmethod
    def curr_version_number(session):
        return session.query(ChangeLog).order_by(ChangeLog.version_number.desc()).first().version_number

# TODO: Start using
# Used for associating additional data, such as open ports, operating system version, etc.
# with a given node
class AdditionalNodeData(Base):
    __tablename__ = 'additional_node_data'

    node_id = Column(Integer, ForeignKey("nodes.id"), primary_key = True)
    data_key = Column(String)
    data_value = Column(String)

class Node(Base):
    __tablename__ = 'nodes'

    # Composite key on node (ID, version number) to allow for keeping a historical record of changes to the graph;
    # this will allow for undo-redo functionality as well as point-in-time playbacks / lookbacks using the change_log table
    # to get the date-time when the change was made
    id = Column(Integer, primary_key = True)
    version_number = Column(Integer, ForeignKey("change_log.version_number"), primary_key = True)
    label = Column(String)
    title = Column(String)
    x_coordinate = Column(Float)
    y_coordinate = Column(Float)
    group = Column(String)
    active = Column(Boolean)

    def serializable_dict(self):
        d = self.__dict__
        del d['_sa_instance_state']

        return d

    @staticmethod
    def from_dict(node):
        return Node(
            id = node.get('id'),
            version_number = node.get('version_number'),
            label = node.get('label'),
            title = node.get('title'),
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
    active = Column(Boolean)

def setup_tables(engine):
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
        
