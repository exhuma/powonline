from flask import Flask
from flask_restful import Resource, Api

from powonline.core import make_dummy_team_dict


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


def make_app():
    '''
    Application factory
    '''
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(Team, '/team')
    return app
