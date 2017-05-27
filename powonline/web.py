from flask import Flask
from flask_restful import Resource, Api

from powonline.core import (
    make_dummy_team_dict,
    make_dummy_station_dict,
    make_dummy_route_dict,
)


class Team(Resource):

    def get(self):
        output = {
            'items': [
                make_dummy_team_dict(name='team2'),
                make_dummy_team_dict(name='team1'),
                make_dummy_team_dict(name='team3'),
            ]
        }
        return output


class Station(Resource):

    def get(self):
        output = {
            'items': [
                make_dummy_station_dict(name='station2'),
                make_dummy_station_dict(name='station1'),
                make_dummy_station_dict(name='station3'),
            ]
        }
        return output


class Route(Resource):

    def get(self):
        output = {
            'items': [
                make_dummy_route_dict(name='route2'),
                make_dummy_route_dict(name='route1'),
                make_dummy_route_dict(name='route3'),
            ]
        }
        return output


def make_app():
    '''
    Application factory
    '''
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(Team, '/team')
    api.add_resource(Station, '/station')
    api.add_resource(Route, '/route')
    return app
