from json import dumps
import logging

from flask import request, make_response
from flask_restful import Resource, marshal_with, fields

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
    USER_SCHEMA,
)


LOG = logging.getLogger(__name__)
STATE_FIELDS = {
    'state': fields.String(attribute=lambda x: x.state.value)
}


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
            teams = list(core.Team.all(DB.session))

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

    def post(self):
        data = request.get_json()

        parsed_data, errors = TEAM_SCHEMA.load(data)
        if errors:
            return errors, 400

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

    def put(self, name):
        data = request.get_json()

        parsed_data, errors = TEAM_SCHEMA.load(data)
        if errors:
            return errors, 400

        output = core.Team.upsert(DB.session, name, parsed_data)
        return Team._single_response(output, 200)

    def delete(self, name):
        core.Team.delete(DB.session, name)
        return '', 204


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

    def post(self):
        data = request.get_json()

        parsed_data, errors = STATION_SCHEMA.load(data)
        if errors:
            return errors, 400

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

    def put(self, name):
        data = request.get_json()

        parsed_data, errors = STATION_SCHEMA.load(data)
        if errors:
            return errors, 400

        output = core.Station.upsert(DB.session, name, parsed_data)
        return Station._single_response(output, 200)

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

    def post(self):
        data = request.get_json()

        parsed_data, errors = ROUTE_SCHEMA.load(data)
        if errors:
            return errors, 400

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

    def put(self, name):
        data = request.get_json()
        parsed_data, errors = ROUTE_SCHEMA.load(data)
        if errors:
            return errors, 400

        output = core.Route.upsert(DB.session, name, parsed_data)
        return Route._single_response(output, 200)

    def delete(self, name):
        core.Route.delete(DB.session, name)
        return '', 204


class StationUserList(Resource):

    def post(self, station_name):
        '''
        Assigns a user to a station
        '''
        data = request.get_json()
        parsed_data, errors = USER_SCHEMA.load(data)
        if errors:
            return errors, 400

        success = core.Station.assign_user(
            DB.session, station_name, parsed_data['name'])
        if success:
            return '', 204
        else:
            return 'User is already assigned to a station', 400


class StationUser(Resource):

    def delete(self, station_name, user_name):
        success = core.Station.unassign_user(
            DB.session, station_name, user_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteTeamList(Resource):

    def post(self, route_name):
        '''
        Assign a team to a route
        '''
        data = request.get_json()
        parsed_data, errors = TEAM_SCHEMA.load(data)
        if errors:
            return errors, 400
        team_name = data['name']

        success = core.Route.assign_team(DB.session, route_name, team_name)
        if success:
            return '', 204
        else:
            return 'Team is already assigned to a route', 400


class RouteTeam(Resource):

    def delete(self, route_name, team_name):
        success = core.Route.unassign_team(DB.session, route_name, team_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class UserRoleList(Resource):

    def post(self, user_name):
        '''
        Assign a role to a user
        '''
        data = request.get_json()
        parsed_data, errors = ROLE_SCHEMA.load(data)
        if errors:
            return errors, 400
        role_name = data['name']

        success = core.User.assign_role(DB.session, user_name, role_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class UserRole(Resource):

    def delete(self, user_name, role_name):
        success = core.User.unassign_role(DB.session, user_name, role_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteStationList(Resource):

    def post(self, route_name):
        '''
        Assign a station to a route
        '''
        data = request.get_json()
        parsed_data, errors = STATION_SCHEMA.load(data)
        if errors:
            return errors, 400
        station_name = data['name']

        success = core.Route.assign_station(
            DB.session, route_name, station_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteStation(Resource):

    def delete(self, route_name, station_name):
        success = core.Route.unassign_station(
            DB.session, route_name, station_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class TeamStation(Resource):

    @marshal_with(STATE_FIELDS)
    def get(self, team_name, station_name):
        state = core.Team.get_station_data(DB.session, team_name, station_name)
        return state, 200


class Assignments(Resource):

    def get(self):
        output = {}
        assignments = core.get_assignments(DB.session)

        route_teams = {}
        for route_name, teams in assignments['teams'].items():
            teams = [TEAM_SCHEMA.dump(team).data for team in teams]
            route_teams[route_name] = teams

        route_stations = {}
        for route_name, stations in assignments['stations'].items():
            stations = [STATION_SCHEMA.dump(station).data
                        for station in stations]
            route_stations[route_name] = stations

        output['stations'] = route_stations
        output['teams'] = route_teams

        output = make_response(dumps(output), 200)
        output.content_type = 'application/json'
        return output


class Dashboard(Resource):
    '''
    Helper resource for the frontend
    '''

    def get(self, station_name):
        output = []
        for team_name, state in core.Station.team_states(
                DB.session, station_name):
            output.append({
                'team': team_name,
                'state': state.value,
                'score': 0
            })

        output = make_response(dumps(output), 200)
        output.content_type = 'application/json'
        return output


class Job(Resource):

    def _action_advance(self, station_name, team_name):
        new_state = core.Team.advance_on_station(
                DB.session, team_name, station_name)
        output = {
            'result': {
                'state': new_state.value
            }
        }
        return output, 200

    def post(self):
        data = request.get_json()
        parsed_data, errors = JOB_SCHEMA.load(data)
        if errors:
            return errors, 400

        action = parsed_data['action']
        func = getattr(self, '_action_%s' % action, None)
        if not func:
            return '%r is an unknown job action' % action, 400
        return func(**parsed_data['args'])
