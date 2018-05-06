from enum import Enum
from functools import wraps
from json import dumps, JSONEncoder
import logging

from flask import request, make_response, jsonify, current_app, g
from flask_restful import Resource, marshal_with, fields
import jwt

from . import core
from .model import DB
from .schema import (
    JOB_SCHEMA,
    ROLE_SCHEMA,
    ROUTE_LIST_SCHEMA,
    ROUTE_SCHEMA,
    STATION_LIST_SCHEMA,
    STATION_SCHEMA,
    TEAM_LIST_SCHEMA,
    TEAM_SCHEMA,
    USER_LIST_SCHEMA,
    USER_SCHEMA,
    USER_SCHEMA_SAFE,
)


LOG = logging.getLogger(__name__)

PERMISSION_MAP = {
    'admin': {
        'admin_routes',
        'admin_stations',
        'admin_teams',
        'manage_permissions',
        'manage_station',
    },
    'station_manager': {
        'manage_station'
    },
}


class ErrorType(Enum):
    INVALID_SCHEMA = 'invalid-schema'


class AccessDenied(Exception):
    pass


def get_user_permissions(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        LOG.debug('No Authorization header present!')
        raise AccessDenied('Access Denied (no "Authorization" header passed)!')
    method, _, token = auth_header.partition(' ')
    method = method.lower().strip()
    token = token.strip()
    if method != 'bearer' or not token:
        LOG.debug('Authorization header does not provide '
                  'a bearer token!')
        raise AccessDenied('Access Denied (not a bearer token)!')
    try:
        jwt_secret = current_app.localconfig.get(
            'security', 'jwt_secret')
        auth_payload = jwt.decode(
            token, jwt_secret, algorithms=['HS256'])
    except jwt.exceptions.DecodeError:
        LOG.info('Bearer token seems to have been tampered with!')
        raise AccessDenied('Access Denied (invalid token)!')

    # Expand the user roles to permissions, collecting them all in one
    # big set.
    user_roles = set(auth_payload.get('roles', []))
    LOG.debug('Bearer token with the following roles: %r', user_roles)
    all_permissions = set()
    for role in user_roles:
        all_permissions |= PERMISSION_MAP.get(role, set())

    LOG.debug('Bearer token grants the following permissions: %r',
              all_permissions)
    return auth_payload, all_permissions


class require_permissions:
    '''
    Decorator for routes.

    All permissions defined in the decorator are required.
    '''

    def __init__(self, *permissions):
        self.permissions = set(permissions)

    def __call__(self, f):
        @wraps(f)
        def fun(*args, **kwargs):
            try:
                auth_payload, all_permissions = get_user_permissions(request)
            except AccessDenied as exc:
                return str(exc), 401

            # by removing the users permissions from the required permissions,
            # we will end up with an empty set if the user is granted access.
            # All remaining permissions are those that the user was not granted
            # (the user is missing those permissions to gain entry).
            # Hence, if the resulting set is non-empty, we block access.
            missing_permissions = self.permissions - all_permissions
            if missing_permissions:
                LOG.debug('User was missing the following permissions: %r',
                          missing_permissions)
                return 'Access Denied (Not enough permissions)!', 401

            # Keep a reference to the JWT payload in the "g" object
            g.jwt_payload = auth_payload

            return f(*args, **kwargs)
        return fun


class MyJsonEncoder(JSONEncoder):

    def default(self, value):
        if isinstance(value, set):
            return list(value)
        elif isinstance(value, Enum):
            return value.value
        super().default(value)


class UserList(Resource):

    @require_permissions('manage_permissions')
    def get(self):
        users = list(core.User.all(DB.session))
        output = {
            'items': users
        }

        parsed_output, errors = USER_LIST_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        output = make_response(parsed_output, 200)
        output.content_type = 'application/json'
        return output

    @require_permissions('manage_permissions')
    def post(self):
        data = request.get_json()

        parsed_data, errors = USER_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.User.create_new(DB.session, parsed_data)
        return User._single_response(output, 201)


class User(Resource):

    @staticmethod
    def _single_response(output, status_code=200):
        parsed_output, errors = USER_SCHEMA_SAFE.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = 'application/json'
        return response

    @require_permissions('manage_permissions')
    def get(self, name):
        user = core.User.get(DB.session, name)
        if not user:
            return 'No such user', 404

        return User._single_response(user, 200)

    @require_permissions('manage_permissions')
    def put(self, name):
        data = request.get_json()

        parsed_data, errors = USER_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.User.upsert(DB.session, name, parsed_data)
        return User._single_response(output, 200)

    @require_permissions('manage_permissions')
    def delete(self, name):
        core.User.delete(DB.session, name)
        return '', 204


class TeamList(Resource):

    def get(self):
        quickfilter = request.args.get('quickfilter', '')
        assigned_to_route = request.args.get('assigned_route', '')
        if quickfilter:
            func_name = 'quickfilter_%s' % quickfilter
            filter_func = getattr(core.Team, func_name, None)
            if not filter_func:
                return '%r is not a known quickfilter!' % quickfilter, 400
            teams = filter_func(DB.session)
        elif assigned_to_route:
            teams = core.Team.assigned_to_route(
                DB.session, assigned_to_route)
        else:
            teams = core.Team.all(DB.session)

        output = {
            'items': teams
        }

        parsed_output, errors = TEAM_LIST_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        output = make_response(parsed_output, 200)
        output.content_type = 'application/json'
        return output

    @require_permissions('admin_teams')
    def post(self):
        data = request.get_json()

        parsed_data, errors = TEAM_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.Team.create_new(DB.session, parsed_data)
        return Team._single_response(output, 201)


class Team(Resource):

    @staticmethod
    def _single_response(output, status_code=200):
        parsed_output, errors = TEAM_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = 'application/json'
        return response

    @require_permissions('admin_teams')
    def put(self, name):
        data = request.get_json()

        parsed_data, errors = TEAM_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.Team.upsert(DB.session, name, parsed_data)
        return Team._single_response(output, 200)

    @require_permissions('admin_teams')
    def delete(self, name):
        core.Team.delete(DB.session, name)
        return '', 204

    def get(self, name):
        team = core.Team.get(DB.session, name)
        if not team:
            return 'No such team', 404

        return Team._single_response(team, 200)


class StationList(Resource):

    def get(self):
        items = list(core.Station.all(DB.session))
        output = {
            'items': items
        }

        parsed_output, errors = STATION_LIST_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        output = make_response(parsed_output, 200)
        output.content_type = 'application/json'
        return output

    @require_permissions('admin_stations')
    def post(self):
        data = request.get_json()

        parsed_data, errors = STATION_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.Station.create_new(DB.session, parsed_data)
        return Station._single_response(output, 201)


class Station(Resource):

    @staticmethod
    def _single_response(output, status_code=200):
        parsed_output, errors = STATION_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = 'application/json'
        return response

    @require_permissions('manage_station')
    def put(self, name):
        auth, permissions = get_user_permissions(request)

        if 'admin' not in auth['roles'] and not core.User.may_access_station(
                DB.session, auth['username'], name):
            return 'Access denied to this station!', 401

        data = request.get_json()

        parsed_data, errors = STATION_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.Station.upsert(DB.session, name, parsed_data)
        return Station._single_response(output, 200)

    @require_permissions('admin_stations')
    def delete(self, name):
        core.Station.delete(DB.session, name)
        return '', 204


class RouteList(Resource):

    def get(self):
        items = list(core.Route.all(DB.session))
        output = {
            'items': items
        }

        parsed_output, errors = ROUTE_LIST_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        output = make_response(parsed_output, 200)
        output.content_type = 'application/json'
        return output

    @require_permissions('admin_routes')
    def post(self):
        data = request.get_json()

        parsed_data, errors = ROUTE_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.Route.create_new(DB.session, parsed_data)
        return Route._single_response(output, 201)


class Route(Resource):

    @staticmethod
    def _single_response(output, status_code=200):
        parsed_output, errors = ROUTE_SCHEMA.dumps(output)
        if errors:
            LOG.critical('Unable to process return value: %r', errors)
            return 'Server was unable to process the response', 500

        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = 'application/json'
        return response

    @require_permissions('admin_routes')
    def put(self, name):
        data = request.get_json()
        parsed_data, errors = ROUTE_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        output = core.Route.upsert(DB.session, name, parsed_data)
        return Route._single_response(output, 200)

    @require_permissions('admin_routes')
    def delete(self, name):
        core.Route.delete(DB.session, name)
        return '', 204


class StationUserList(Resource):

    def _assign_user_to_station(self, station_name):
        data = request.get_json()
        user, errors = USER_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400
        success = core.Station.assign_user(
            DB.session, station_name, user['name'])
        if success:
            return '', 204
        else:
            return 'Station is already assigned to that user', 400

    def _assign_station_to_user(self, user_name):
        data = request.get_json()
        station, errors = STATION_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400
        success = core.User.assign_station(
            DB.session, user_name, station['name'])
        if success:
            return '', 204
        else:
            return 'Station is already assigned to that user', 400

    def _list_station_by_user(self, user_name):
        user = core.User.get(DB.session, user_name)
        if not user:
            return 'No such user', 404
        all_stations = core.Station.all(DB.session)
        user_stations = {station.name for station in user.stations}
        output = []
        for station in all_stations:
            output.append((station.name, station.name in user_stations))
        return jsonify(output)

    @require_permissions('manage_permissions')
    def get(self, station_name=None, user_name=None):
        if user_name and not station_name:
            return self._list_station_by_user(user_name)
        elif station_name and not user_name:
            return self._list_user_by_station(station_name)
        else:
            return 'Unexpected input!', 400

    @require_permissions('manage_permissions')
    def post(self, station_name=None, user_name=None):
        '''
        Assigns a user to a station
        '''
        if user_name and not station_name:
            return self._assign_station_to_user(user_name)
        elif station_name and not user_name:
            return self._assign_user_to_station(station_name)
        else:
            return 'Unexpected input!', 400


class StationUser(Resource):

    @require_permissions('manage_permissions')
    def get(self, user_name=None, station_name=None):
        user = core.User.get(DB.session, user_name)
        if not user:
            return 'No such user', 404
        stations = {_.name for _ in user.stations}

        if station_name in stations:
            return jsonify(True)
        else:
            return jsonify(False)

    @require_permissions('manage_permissions')
    def delete(self, station_name, user_name):
        success = core.Station.unassign_user(
            DB.session, station_name, user_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteTeamList(Resource):

    @require_permissions('admin_routes')
    def post(self, route_name):
        '''
        Assign a team to a route
        '''
        data = request.get_json()
        if not data:
            return 'Payload required!', 400
        team_name = data['name']

        success = core.Route.assign_team(DB.session, route_name, team_name)
        if success:
            return '', 204
        else:
            return 'Team is already assigned to a route', 400


class RouteTeam(Resource):

    @require_permissions('admin_routes')
    def delete(self, route_name, team_name):
        success = core.Route.unassign_team(DB.session, route_name, team_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class UserRoleList(Resource):

    @require_permissions('manage_permissions')
    def get(self, user_name):
        user = core.User.get(DB.session, user_name)
        if not user:
            return 'No such user', 404
        all_roles = core.Role.all(DB.session)
        user_roles = {role.name for role in user.roles}
        output = []
        for role in all_roles:
            output.append((role.name, role.name in user_roles))
        return jsonify(output)

    @require_permissions('manage_permissions')
    def post(self, user_name):
        '''
        Assign a role to a user
        '''
        data = request.get_json()
        parsed_data, errors = ROLE_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400
        role_name = data['name']

        success = core.User.assign_role(DB.session, user_name, role_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class UserRole(Resource):

    @require_permissions('manage_permissions')
    def delete(self, user_name, role_name):
        success = core.User.unassign_role(DB.session, user_name, role_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500

    @require_permissions('manage_permissions')
    def get(self, user_name, role_name):
        user = core.User.get(DB.session, user_name)
        if not user:
            return 'No such user', 404
        roles = {_.name for _ in user.roles}

        if role_name in roles:
            return jsonify(True)
        else:
            return jsonify(False)


class RouteStationList(Resource):

    @require_permissions('admin_routes')
    def post(self, route_name):
        '''
        Assign a station to a route
        '''
        data = request.get_json()
        parsed_data, errors = STATION_SCHEMA.load(data)
        station_name = data['name']

        success = core.Route.assign_station(
            DB.session, route_name, station_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteStation(Resource):

    @require_permissions('admin_routes')
    def delete(self, route_name, station_name):
        success = core.Route.unassign_station(
            DB.session, route_name, station_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class TeamStation(Resource):

    def get(self, team_name, station_name=None):
        if station_name is None:
            items = core.Team.stations(DB.session, team_name)
            output = {
                'items': sorted(items, key=lambda x: x.name)
            }

            parsed_output, errors = STATION_LIST_SCHEMA.dumps(output)
            if errors:
                LOG.critical('Unable to process return value: %r', errors)
                return 'Server was unable to process the response', 500

            output = make_response(parsed_output, 200)
            output.content_type = 'application/json'
            return output
        else:
            state = core.Team.get_station_data(DB.session, team_name, station_name)
            return {
                'state': state.state.value
            }, 200


class Assignments(Resource):

    def get(self):
        data = core.get_assignments(DB.session)

        out_stations = {}
        for route_name, stations in data['stations'].items():
            out_stations[route_name] = [STATION_SCHEMA.dump(station)[0]
                                        for station in stations]

        out_teams = {}
        for route_name, teams in data['teams'].items():
            out_teams[route_name] = [TEAM_SCHEMA.dump(team)[0]
                                     for team in teams]

        output = {
            'stations': out_stations,
            'teams': out_teams
        }

        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = 'application/json'
        return output


class Scoreboard(Resource):
    '''
    Helper resource for the frontend
    '''

    def get(self):
        output = list(core.scoreboard(DB.session))
        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = 'application/json'
        return output


class Dashboard(Resource):
    '''
    Helper resource for the frontend
    '''

    def get(self, station_name):
        output = []
        for team_name, state, score in core.Station.team_states(
                DB.session, station_name):
            output.append({
                'team': team_name,
                'state': state.value,
                'score': score
            })

        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = 'application/json'
        return output


class GlobalDashboard(Resource):
    '''
    The global state of each team on each station of the event.
    '''

    def get(self):
        output = core.global_dashboard(DB.session)
        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = 'application/json'
        return output


class Job(Resource):

    def _action_advance(self, station_name, team_name):
        auth, permissions = get_user_permissions(request)

        pusher_channel = current_app.localconfig.get(
            'pusher_channels', 'team_station_state',
            default='team_station_state_dev')

        if 'admin_stations' in permissions or (
                'manage_station' in permissions and
                core.User.may_access_station(
                    DB.session, auth['username'], station_name)):
            new_state = core.Team.advance_on_station(
                    DB.session, team_name, station_name)
            output = {
                'result': {
                    'state': new_state.value
                }
            }
            current_app.pusher.trigger(
                pusher_channel,
                'state-change',
                {
                    'station': station_name,
                    'team': team_name,
                    'new_state': new_state.value
                }
            )
            return output, 200
        else:
            return 'Access denied to this station!', 401

    def _action_set_score(self, station_name, team_name, score):
        score = int(score, 10)
        auth, permissions = get_user_permissions(request)

        pusher_channel = current_app.localconfig.get(
            'pusher_channels', 'team_station_state',
            default='team_station_state_dev')

        if 'admin_stations' in permissions or (
                'manage_station' in permissions and
                core.User.may_access_station(
                    DB.session, auth['username'], station_name)):
            LOG.info('Setting score of %s on %s to %s (by user: %s)',
                     team_name, station_name, score, auth['username'])
            new_score = core.Team.set_station_score(
                DB.session, team_name, station_name, score)
            output = {
                'new_score': new_score,
            }
            current_app.pusher.trigger(
                pusher_channel,
                'score-change',
                {
                    'station': station_name,
                    'team': team_name,
                    'new_score': new_score,
                }
            )
            return output, 200
        else:
            return 'Access denied to this station!', 401

    def _action_set_questionnaire_score(self, station_name, team_name, score):
        auth, permissions = get_user_permissions(request)

        pusher_channel = current_app.localconfig.get(
            'pusher_channels', 'team_station_state',
            default='team_station_state_dev')

        if 'admin_stations' in permissions or (
                'manage_station' in permissions and
                core.User.may_access_station(
                    DB.session, auth['username'], station_name)):
            LOG.info('Setting questionnaire score of %s on %s to %s ('
                     'by user: %s)',
                     team_name, station_name, score, auth['username'])
            try:
                new_score = core.set_questionnaire_score(
                    current_app.localconfig,
                    DB.session, team_name, station_name, score)
            except KeyError:
                return ('No questionnaire assigned to station %r!'
                        % station_name, 500)
            output = {
                'new_score': new_score,
            }
            current_app.pusher.trigger(
                pusher_channel,
                'questionnaire-score-change',
                {
                    'stationName': station_name,
                    'teamName': team_name,
                    'score': new_score,
                }
            )
            return output, 200
        else:
            return 'Access denied to this station!', 401

    @require_permissions('manage_station')
    def post(self):
        data = request.get_json()
        parsed_data, errors = JOB_SCHEMA.load(data)
        if errors:
            return {'error': ErrorType.INVALID_SCHEMA.value,
                    'errors': errors}, 400

        action = parsed_data['action']
        func = getattr(self, '_action_%s' % action, None)
        if not func:
            LOG.debug('Unknown job %r requested!', parsed_data['action'])
            return '%r is an unknown job action' % action, 400
        return func(**parsed_data['args'])
