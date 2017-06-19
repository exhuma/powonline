from datetime import datetime
from enum import Enum
import logging

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
    create_engine,
    func,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import sqlalchemy.types as types


ENGINE = create_engine('postgresql://exhuma@/powonline', echo=True)
LOG = logging.getLogger(__name__)
Base = declarative_base()


class TeamState(Enum):
    UNKNOWN = 'unknown'
    ARRIVED = 'arrived'
    FINISHED = 'finished'


class TeamStateType(types.TypeDecorator):

    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return value.value

    def process_result_value(self, value, dialect):
        return TeamState(value)


class Team(Base):
    __tablename__ = 'team'

    name = Column(Unicode, primary_key=True, nullable=False)
    email = Column(Unicode, nullable=False)
    order = Column(Integer, nullable=False, server_default='500')
    cancelled = Column(Boolean, nullable=False, server_default='false')
    contact = Column(Unicode)
    phone = Column(Unicode)
    comments = Column(Unicode)
    is_confirmed = Column(Boolean, nullable=False, server_default='false')
    confirmation_key = Column(Unicode, nullable=False, server_default='')
    accepted = Column(Boolean, nullable=False, server_default='false')
    completed = Column(Boolean, nullable=False, server_default='false')
    inserted = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())
    num_vegetarians = Column(Integer)
    num_participants = Column(Integer)
    planned_start_time = Column(DateTime)
    effective_start_time = Column(DateTime)
    finish_time = Column(DateTime)
    route_name = Column(
        Unicode,
        ForeignKey('route.name', onupdate='CASCADE', ondelete='SET NULL'))

    route = relationship('Route', backref='teams')

    def __init__(self, name='Example Team'):
        self.name = name
        self.email = 'example@example.com'
        self.order = 0
        self.cancelled = False
        self.contact = 'John Doe'
        self.phone = '1234'
        self.comments = ''
        self.is_confirmed = True
        self.confirmation_key = 'abc'
        self.accepted = True
        self.completed = False
        self.inserted = datetime.now()
        self.updated = None
        self.num_vegetarians = 3
        self.num_participants = 10
        self.planned_start_time = None
        self.effective_start_time = None
        self.finish_time = None

    stations = relationship('Station', secondary='team_station_state',
                            viewonly=True)  # uses an AssociationObject

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return "Team(name=%r)" % self.name


class Station(Base):
    __tablename__ = 'station'
    name = Column(Unicode, primary_key=True, nullable=False)
    contact = Column(Unicode)
    phone = Column(Unicode)
    is_start = Column(Boolean, nullable=False, server_default='false')
    is_end = Column(Boolean, nullable=False, server_default='false')

    def __init__(self):
        self.name = 'Example Station'
        self.contact = 'Example Contact'
        self.phone = '12345'
        self.is_start = False
        self.is_end = False

    users = relationship('User',
                         secondary='user_station',
                         back_populates='stations',
                         collection_class=set)

    teams = relationship('Team', secondary='team_station_state',
                         viewonly=True)  # uses an AssociationObject

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return "Station(name=%r)" % self.name


class Route(Base):
    __tablename__ = 'route'

    name = Column(Unicode, primary_key=True)

    def __init__(self):
        self.name = 'Example Station'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class User(Base):
    __tablename__ = 'user'
    name = Column(Unicode, primary_key=True)  # TODO: Should the name be the PK? Email or ID would be better.

    stations = relationship('Station',
                            secondary='user_station',
                            back_populates='users',
                            collection_class=set)


class Role(Base):
    __tablename__ = 'role'
    name = Column(Unicode, primary_key=True)

    def __init__(self):
        self.name = 'Example Station'


class TeamStation(Base):
    __tablename__ = 'team_station_state'

    team_name = Column(Unicode, ForeignKey(
        'team.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    station_name = Column(Unicode, ForeignKey(
        'station.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    state = Column(TeamStateType, default=TeamState.UNKNOWN)
    score = Column(Integer, nullable=True, default=None)
    updated = Column(DateTime(timezone=True), nullable=False,
                     default=datetime.now(), server_default=func.now())

    team = relationship("Team")
    station = relationship("Station", backref='states')

    def __init__(self, team_name, station_name, state=TeamState.UNKNOWN):
        self.team_name = team_name
        self.station_name = station_name
        self.state = state


class RouteStation(Base):
    __tablename__ = 'route_station'

    route_name = Column(Unicode, ForeignKey(
        'route.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    station_name = Column(Unicode, ForeignKey(
        'station.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    score = Column(Integer, nullable=True, default=None)
    updated = Column(DateTime(timezone=True), nullable=False,
                     default=datetime.now(), server_default=func.now())

    route = relationship("Route")
    station = relationship("Station", backref='stations')

    def __init__(self, route_name, station_name):
        self.route_name = route_name
        self.station_name = station_name

user_station_table = Table(
    'user_station',
    DB.metadata,
    Column('user_name', Unicode, ForeignKey(
        'user.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True),
    Column('station_name', Unicode, ForeignKey(
        'station.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True),
)


class Job:
    def __init__(self):
        self.action = 'example_action'
        self.args = {}
