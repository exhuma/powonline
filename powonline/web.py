import logging

import click
from flask import Flask
from flask_restful import Api

from .config import default
from .model import DB
from .pusher import PusherWrapper
from .resources import (Assignments, Dashboard, GlobalDashboard, Job, Route,
                        RouteList, RouteStation, RouteStationList, RouteTeam,
                        RouteTeamList, Scoreboard, Station, StationList,
                        StationUser, StationUserList, Team, TeamList,
                        TeamStation, User, UserList, UserRole, UserRoleList)
from .rootbp import rootbp

LOG = logging.getLogger(__name__)


def make_app(config=None):
    '''
    Application factory
    '''
    app = Flask(__name__)
    api = Api(app)

    if not config:
        config = default()

    app.localconfig = config
    app.secret_key = config.get('security', 'secret_key')
    app.register_blueprint(rootbp)
    app.pusher = PusherWrapper.create(
        config.get('pusher', 'app_id', fallback=''),
        config.get('pusher', 'key', fallback=''),
        config.get('pusher', 'secret', fallback=''),
    )

    api.add_resource(Assignments, '/assignments')
    api.add_resource(TeamList, '/team')
    api.add_resource(Team, '/team/<name>')
    api.add_resource(StationList, '/station')
    api.add_resource(Station, '/station/<name>')
    api.add_resource(RouteList, '/route')
    api.add_resource(Route, '/route/<name>')
    api.add_resource(StationUserList,
                     '/station/<station_name>/users',
                     '/user/<user_name>/stations')
    api.add_resource(StationUser,
                     '/station/<station_name>/users/<user_name>',
                     '/user/<user_name>/stations/<station_name>')
    api.add_resource(RouteTeamList, '/route/<route_name>/teams')
    api.add_resource(RouteTeam, '/route/<route_name>/teams/<team_name>')
    api.add_resource(UserList, '/user')
    api.add_resource(User, '/user/<name>')
    api.add_resource(UserRoleList, '/user/<user_name>/roles')
    api.add_resource(UserRole, '/user/<user_name>/roles/<role_name>')
    api.add_resource(RouteStationList, '/route/<route_name>/stations')
    api.add_resource(RouteStation,
                     '/route/<route_name>/stations/<station_name>')
    api.add_resource(TeamStation,
                     '/team/<team_name>/stations/<station_name>',
                     '/team/<team_name>/stations',
                     '/station/<station_name>/teams/<team_name>',
                     )
    api.add_resource(Scoreboard, '/scoreboard')
    api.add_resource(Dashboard, '/station/<station_name>/dashboard')
    api.add_resource(GlobalDashboard, '/dashboard')
    api.add_resource(Job, '/job')

    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('db', 'dsn')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    DB.init_app(app)

    return app
