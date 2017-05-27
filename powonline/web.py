from flask import Flask, request
from flask_restful import Resource, Api

from powonline.core import (
    ROUTE_STATION_MAP,
    TEAM_ROUTE_MAP,
    TEAM_STATION_MAP,
    TeamState,
    USER_ROLES,
    USER_STATION_MAP,
    advance,
    make_dummy_route_dict,
    make_dummy_station_dict,
    make_dummy_team_dict,
)


class TeamList(Resource):

    def get(self):
        output = {
            'items': [
                make_dummy_team_dict(name='team2'),
                make_dummy_team_dict(name='team1'),
                make_dummy_team_dict(name='team3'),
            ]
        }
        return output

    def post(self):
        new_team = request.get_json()
        return new_team, 201


class Team(Resource):

    def put(self, name):
        output = make_dummy_team_dict(name=name)
        output.update(request.get_json())
        return output

    def delete(self, name):
        return '', 204


class StationList(Resource):

    def get(self):
        output = {
            'items': [
                make_dummy_station_dict(name='station2'),
                make_dummy_station_dict(name='station1'),
                make_dummy_station_dict(name='station3'),
            ]
        }
        return output

    def post(self):
        new_station = request.get_json()
        return new_station, 201


class Station(Resource):

    def put(self, name):
        output = make_dummy_station_dict(name=name)
        output.update(request.get_json())
        return output

    def delete(self, name):
        return '', 204


class RouteList(Resource):

    def get(self):
        output = {
            'items': [
                make_dummy_route_dict(name='route2'),
                make_dummy_route_dict(name='route1'),
                make_dummy_route_dict(name='route3'),
            ]
        }
        return output


    def post(self):
        new_route = request.get_json()
        return new_route, 201


class Route(Resource):

    def put(self, name):
        output = make_dummy_route_dict(name=name)
        output.update(request.get_json())
        return output

    def delete(self, name):
        return '', 204


class StationUserList(Resource):

    def post(self, station_name):
        new_assignment = request.get_json()
        user_name = new_assignment['name']
        assigned_station = USER_STATION_MAP.get(user_name)
        if assigned_station:
            return 'User is already assigned to a station', 400
        USER_STATION_MAP[user_name] = station_name
        return '', 204


class StationUser(Resource):

    def delete(self, station_name, user_name):
        if station_name in USER_STATION_MAP:
            del(USER_STATION_MAP[station_name])
        return '', 204


class RouteTeamList(Resource):

    def post(self, route_name):
        new_assignment = request.get_json()
        team_name = new_assignment['name']
        assigned_route = TEAM_ROUTE_MAP.get(team_name)
        if assigned_route:
            return 'Team is already assigned to a route', 400
        TEAM_ROUTE_MAP[team_name] = route_name
        return '', 204


class RouteTeam(Resource):

    def delete(self, route_name, team_name):
        if team_name in TEAM_ROUTE_MAP:
            del(TEAM_ROUTE_MAP[team_name])
        return '', 204


class UserRoleList(Resource):

    def post(self, user_name):
        new_assignment = request.get_json()
        role_name = new_assignment['name']
        assigned_roles = USER_ROLES.get(user_name, set())
        assigned_roles.add(role_name)
        return '', 204


class UserRole(Resource):

    def delete(self, user_name, role_name):
        roles = USER_ROLES.get(user_name, set())
        if role_name in roles:
            roles.remove(role_name)
        return '', 204


class RouteStationList(Resource):

    def post(self, route_name):
        new_assignment = request.get_json()
        station_name = new_assignment['name']
        assigned_routes = ROUTE_STATION_MAP.get(station_name, set())
        assigned_routes.add(route_name)
        return '', 204


class RouteStation(Resource):

    def delete(self, route_name, station_name):
        assigned_routes = ROUTE_STATION_MAP.get(station_name, set())
        if route_name in assigned_routes:
            assigned_routes.remove(route_name)
        return '', 204


class TeamStation(Resource):

    def get(self, team_name, station_name):
        state = TEAM_STATION_MAP.get(team_name, {}).get(station_name, {})
        if 'state' not in state:
            state['state'] = TeamState.UNKNOWN.value
        return state, 200


class Job(Resource):

    def post(self):
        allowed_actions = ['advance']
        data = request.get_json()
        args = data['args']
        action = data['action']
        station_name = args['station_name']
        team_name = args['team_name']
        if action not in allowed_actions:
            return '%r is an unknown job' % action

        if action == 'advance':
            new_state = advance(team_name, station_name)
            output = {
                'result': {
                    'state': new_state.value
                }
            }
            return output, 200
        else:
            return 'Unknown error', 500


def make_app():
    '''
    Application factory
    '''
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(TeamList, '/team')
    api.add_resource(Team, '/team/<name>')
    api.add_resource(StationList, '/station')
    api.add_resource(Station, '/station/<name>')
    api.add_resource(RouteList, '/route')
    api.add_resource(Route, '/route/<name>')
    api.add_resource(StationUserList, '/station/<station_name>/users')
    api.add_resource(StationUser, '/station/<station_name>/users/<user_name>')
    api.add_resource(RouteTeamList, '/route/<route_name>/teams')
    api.add_resource(RouteTeam, '/route/<route_name>/teams/<team_name>')
    api.add_resource(UserRoleList, '/user/<user_name>/roles')
    api.add_resource(UserRole, '/user/<user_name>/roles/<role_name>')
    api.add_resource(RouteStationList, '/route/<route_name>/stations')
    api.add_resource(RouteStation,
                     '/route/<route_name>/stations/<station_name>')
    api.add_resource(TeamStation,
                     '/team/<team_name>/stations/<station_name>',
                     '/station/<station_name>/teams/<team_name>',
                     )
    api.add_resource(Job, '/job')
    return app
