from flask import Flask
from flask_restful import Api
import logging

from .resources import (
    Assignments,
    Dashboard,
    GlobalDashboard,
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
from .model import DB
from .pusher import PusherWrapper
from .rootbp import rootbp


LOG = logging.getLogger(__name__)


def make_app(config):
    '''
    Application factory
    '''
    app = Flask(__name__)
    api = Api(app)

    static_folder = config.get('app', 'static_folder', default='')
    if not static_folder:
        LOG.warning('No app.static_folder specified in config! '
                    'Instance will have no working frontend!')
    else:
        from flask import send_from_directory
        from jinja2 import ChoiceLoader, FileSystemLoader
        from os.path import join, dirname
        loader = ChoiceLoader([
            FileSystemLoader(join(static_folder)),
            FileSystemLoader(join(dirname(__file__), 'templates'))
        ])
        app.jinja_loader = loader
        app.static_folder = static_folder

        @app.route('/static/js/<path:path>')
        def js(path):
            js_folder = join(static_folder, 'static', 'js')
            return send_from_directory(js_folder, path)

        @app.route('/static/css/<path:path>')
        def css(path):
            css_folder = join(static_folder, 'static', 'css')
            return send_from_directory(css_folder, path)

    app.localconfig = config
    app.register_blueprint(rootbp)
    app.pusher = PusherWrapper.create(
        config.get('pusher', 'app_id', default=''),
        config.get('pusher', 'key', default=''),
        config.get('pusher', 'secret', default=''),
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
    api.add_resource(Dashboard, '/station/<station_name>/dashboard')
    api.add_resource(GlobalDashboard, '/dashboard')
    api.add_resource(Job, '/job')

    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('db', 'dsn')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    DB.init_app(app)

    return app
