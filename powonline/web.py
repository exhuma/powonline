from flask import Flask
from flask_restful import Api

from .resources import (
    Assignments,
    Dashboard,
    Job,
    Route,
    RouteList,
    RouteStation,
    RouteStationList,
    RouteTeam,
    RouteTeamList,
    Station,
    StationList,
    StationUser,
    StationUserList,
    Team,
    TeamList,
    TeamStation,
    User,
    UserList,
    UserRole,
    UserRoleList,
)
from .rootbp import rootbp
from .model import DB


def make_app(config):
    '''
    Application factory
    '''
    app = Flask(__name__)
    api = Api(app)

    app.localconfig = config
    app.register_blueprint(rootbp)

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
    api.add_resource(Dashboard, '/station/<station_name>/dashboard')
    api.add_resource(Job, '/job')

    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('db', 'dsn')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    DB.init_app(app)

    return app
