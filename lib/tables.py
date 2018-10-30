import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, Float, DateTime, String

Base = declarative_base()

class ChangeLog(Base):
    __tablename__ = 'change_log'

    # Authoritative graph version number (i.e. logical time)
    version_number = Column(Integer, primary_key=True)

    # Index on date_time to allow efficient data-based queries
    date_time = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class Node(Base):
    __tablename__ = 'nodes'

    # Composite key on node (ID, version number) to allow for keeping a historical record of changes to the graph;
    # this will allow for undo-redo functionality as well as point-in-time playbacks / lookbacks using the change_log table
    # to get the date-time when the change was made
    id = Column(Integer, primary_key=True)
    version_number = Column(Integer, ForeignKey("change_log.version_number"), primary_key=True)
    label = Column(String)
    title = Column(String)
    x_coordinate = Column(Float)
    y_coordinate = Column(Float)
    group = Column(String)

    def json(self):
        # TODO: Add to Node; work in Edges; or do via a query
        pass
    
class Edge(Base):
    __tablename__ = 'edges'

    source_node_id = Column(Integer, ForeignKey("nodes.id"), primary_key=True)
    destination_node_id = Column(Integer, ForeignKey("nodes.id"), primary_key=True)
    version_number = Column(Integer, ForeignKey("change_log.version_number"), primary_key=True)

def setup_tables(engine):
    # TODO: Add check on whether the tables exist already
    Base.metadata.create_all(engine)
