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
from .model import DB, get_sessionmaker, User as DBUser


class Powonline(Flask):

    def __init__(self, import_name, config, *args, **kwargs):
        super().__init__(import_name)
        self.localconfig = config

    def set_password(self, username, password):
        '''
        Sets a password for a user in the database. If the user is missing, it
        will be added.

        This is intended as admin utility and should not be used from a
        web-context!

        TODO: raise an exception if this is called from a web context
        '''
        Session = get_sessionmaker(self.localconfig)
        session = Session()

        query = session.query(DBUser).filter_by(name=username)
        existing_user = query.one_or_none()
        if not existing_user:
            user = DBUser(username, password)
            session.add(user)
        else:
            user = existing_user
        user.setpw(password)
        session.commit()
        return user


def make_app(config):
    '''
    Application factory
    '''
    app = Powonline(__name__, config)
    api = Api(app)

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
