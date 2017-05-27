from flask import Flask, request
from flask_restful import Resource, Api

from powonline.core import (
    make_dummy_route_dict,
    make_dummy_station_dict,
    make_dummy_team_dict,
    USER_STATION_MAP,
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


class UserStationList(Resource):

    def post(self, username):
        new_assignment = request.get_json()
        assigned_station = USER_STATION_MAP.get(username)
        if assigned_station:
            return 'User is already assigned to a station', 400
        USER_STATION_MAP[username] = new_assignment['name']
        return '', 204


class UserStation(Resource):

    def delete(self, username, station_name):
        if station_name in USER_STATION_MAP:
            del(USER_STATION_MAP[station_name])
        return '', 204


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
    api.add_resource(UserStationList, '/user/<username>/stations')
    api.add_resource(UserStation, '/user/<username>/stations/<station_name>')
    return app
