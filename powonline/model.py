from datetime import datetime
from enum import Enum
import logging

from bcrypt import gensalt, hashpw, checkpw
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
    func,
    Table,
)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship
import sqlalchemy.types as types


LOG = logging.getLogger(__name__)
DB = SQLAlchemy()


class TeamState(Enum):
    UNKNOWN = 'unknown'
    ARRIVED = 'arrived'
    FINISHED = 'finished'
    UNREACHABLE = 'unreachable'


class TeamStateType(types.TypeDecorator):

    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return value.value

    def process_result_value(self, value, dialect):
        return TeamState(value)


class Team(DB.Model):
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

    route = relationship('Route', back_populates='teams')
    stations = relationship('Station', secondary='team_station_state',
                            viewonly=True)  # uses an AssociationObject

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return "Team(name=%r)" % self.name


class Station(DB.Model):
    __tablename__ = 'station'
    name = Column(Unicode, primary_key=True, nullable=False)
    contact = Column(Unicode)
    phone = Column(Unicode)
    order = Column(Integer, nullable=False, server_default='500')
    is_start = Column(Boolean, nullable=False, server_default='false')
    is_end = Column(Boolean, nullable=False, server_default='false')

    routes = relationship('Route',
                          secondary='route_station',
                          back_populates='stations',
                          collection_class=set)

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


class Route(DB.Model):
    __tablename__ = 'route'

    name = Column(Unicode, primary_key=True)
    color = Column(Unicode)

    teams = relationship('Team', back_populates='route', collection_class=set)
    stations = relationship('Station',
                            secondary='route_station',
                            back_populates='routes',
                            collection_class=set)

    def __repr__(self):
        return "Route(name=%r)" % self.name

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class User(DB.Model):
    __tablename__ = 'user'
    name = Column(Unicode, primary_key=True)
    password = Column(BYTEA)
    password_is_plaintext = Column(
        Boolean, nullable=False, server_default='false')

    def __init__(self, name, password):
        self.name = name
        self.password = hashpw(password.encode('utf8'), gensalt())
        self.password_is_plaintext = False

    def checkpw(self, password):
        if self.password_is_plaintext:
            self.password = hashpw(password.encode('utf8'), gensalt())
            self.password_is_plaintext = False
        return checkpw(password.encode('utf8'), self.password)

    def setpw(self, new_password):
        self.password = hashpw(new_password.encode('utf8'), gensalt())
        self.password_is_plaintext = False

    roles = relationship('Role',
                         secondary='user_role',
                         back_populates='users',
                         collection_class=set)
    stations = relationship('Station',
                            secondary='user_station',
                            back_populates='users',
                            collection_class=set)


class Role(DB.Model):
    __tablename__ = 'role'
    name = Column(Unicode, primary_key=True)
    users = relationship('User',
                         secondary='user_role',
                         back_populates='roles',
                         collection_class=set)

    def __init__(self):
        self.name = 'Example Station'


class TeamStation(DB.Model):
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


route_station_table = Table(
    'route_station',
    DB.metadata,
    Column('route_name', Unicode, ForeignKey(
        'route.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True),
    Column('station_name', Unicode, ForeignKey(
        'station.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True),
    Column('updated', DateTime(timezone=True), nullable=False,
           default=datetime.now(), server_default=func.now()),
)

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

user_role_table = Table(
    'user_role',
    DB.metadata,
    Column('user_name', Unicode, ForeignKey(
        'user.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True),
    Column('role_name', Unicode, ForeignKey(
        'role.name', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True),
)


class Job:
    def __init__(self):
        self.action = 'example_action'
        self.args = {}
