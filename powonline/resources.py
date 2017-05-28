from flask import request
from flask_restful import Resource, marshal_with, fields

from . import core


STATE_FIELDS = {
    'state': fields.String(attribute=lambda x: x['state'].value)
}


class TeamList(Resource):

    def get(self):
        teams = list(core.Team.all())
        output = {
            'items': teams
        }
        return output

    def post(self):
        data = request.get_json()
        # TODO: sanitize data
        new_team = core.Team.create_new(data)
        return new_team, 201


class Team(Resource):

    def put(self, name):
        data = request.get_json()
        # TODO: sanitize data
        output = core.Team.upsert(name, data)
        return output

    def delete(self, name):
        # TODO: sanitize data
        core.Team.delete(name)
        return '', 204


class StationList(Resource):

    def get(self):
        items = list(core.Station.all())
        output = {
            'items': items
        }
        return output

    def post(self):
        data = request.get_json()
        # TODO: sanitize data
        new_station = core.Station.create_new(data)
        return new_station, 201


class Station(Resource):

    def put(self, name):
        data = request.get_json()
        # TODO: sanitize data
        output = core.Station.upsert(name, data)
        return output

    def delete(self, name):
        # TODO: sanitize data
        core.Station.delete(name)
        return '', 204


class RouteList(Resource):

    def get(self):
        items = list(core.Route.all())
        output = {
            'items': items
        }
        return output

    def post(self):
        data = request.get_json()
        # TODO: sanitize data
        new_route = core.Route.create_new(data)
        return new_route, 201


class Route(Resource):

    def put(self, name):
        data = request.get_json()
        # TODO: sanitize data
        output = core.Route.upsert(name, data)
        return output

    def delete(self, name):
        # TODO: sanitize data
        core.Route.delete(name)
        return '', 204


class StationUserList(Resource):

    def post(self, station_name):
        '''
        Assigns a user to a station
        '''
        new_assignment = request.get_json()
        user_name = new_assignment['name']
        success = core.Station.assign_user(station_name, user_name)
        if success:
            return '', 204
        else:
            return 'User is already assigned to a station', 400


class StationUser(Resource):

    def delete(self, station_name, user_name):
        success = core.Station.unassign_user(station_name, user_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteTeamList(Resource):

    def post(self, route_name):
        '''
        Assign a team to a route
        '''
        new_assignment = request.get_json()
        team_name = new_assignment['name']

        success = core.Route.assign_team(route_name, team_name)
        if success:
            return '', 204
        else:
            return 'Team is already assigned to a route', 400


class RouteTeam(Resource):

    def delete(self, route_name, team_name):
        success = core.Route.unassign_team(route_name, team_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class UserRoleList(Resource):

    def post(self, user_name):
        '''
        Assign a role to a user
        '''
        new_assignment = request.get_json()
        role_name = new_assignment['name']
        success = core.User.assign_role(user_name, role_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class UserRole(Resource):

    def delete(self, user_name, role_name):
        success = core.User.unassign_role(user_name, role_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteStationList(Resource):

    def post(self, route_name):
        '''
        Assign a station to a route
        '''
        new_assignment = request.get_json()
        station_name = new_assignment['name']
        success = core.Route.assign_station(route_name, station_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class RouteStation(Resource):

    def delete(self, route_name, station_name):
        success = core.Route.unassign_station(route_name, station_name)
        if success:
            return '', 204
        else:
            return 'Unexpected error!', 500


class TeamStation(Resource):

    @marshal_with(STATE_FIELDS)
    def get(self, team_name, station_name):
        state = core.Team.get_station_data(team_name, station_name)
        return state, 200


class Job(Resource):

    def _action_advance(self, station_name, team_name):
        new_state = core.Team.advance_on_station(team_name, station_name)
        output = {
            'result': {
                'state': new_state.value
            }
        }
        return output, 200

    def post(self):
        data = request.get_json()
        action = data['action']
        func = getattr(self, '_action_%s' % action, None)
        if not func:
            return '%r is an unknown job action' % action, 400
        return func(**data['args'])
