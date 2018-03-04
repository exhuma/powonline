"""
This module contains tests for features implemented mainly for helping the vuejs
based frontens.
"""
from textwrap import dedent
import json

from config_resolver import Config
from flask_testing import TestCase

from powonline.web import make_app
import powonline.model as model


def drop_all_except(dct, *keep):
    '''
    Given a dictionary, and a list of keys from that dictionary, this function
    will drop all keys from the dictionary *except* those given in the list
    *keep*.

    This is used to make testing larger dictionary structures a bit easier (but
    less complete).
    '''
    dict_keys = list(dct.keys())
    for key in dict_keys:
        if key not in keep:
            del(dct[key])


def here(localname):
    from os.path import join, dirname
    return join(dirname(__file__), localname)


class TestFrontendHelpers(TestCase):

    SQLALCHEMY_DATABASE_URI = 'postgresql://exhuma@/powonline_testing'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

    def create_app(self):
        config = Config('mamerwiselen', 'powonline', filename='test.ini')
        config.read_string(dedent(
            '''\
            [db]
            dsn = %s

            [security]
            jwt_secret = %s
            ''' % (
                TestFrontendHelpers.SQLALCHEMY_DATABASE_URI,
                'testing'
            )))
        return make_app(config)

    def setUp(self):
        self.app = self.client  # <-- avoiding unrelated diffs for now.
                                #     Can be removed in a later commit
        model.DB.create_all()

        with open(here('seed.sql')) as seed:
            model.DB.session.execute(seed.read())
            model.DB.session.commit()

        self.maxDiff = None

    def tearDown(self):
        model.DB.session.remove()
        model.DB.drop_all()

    def test_fetch_assignments_api(self):
        result = self.app.get('/assignments')
        result_data = json.loads(result.data.decode(result.charset))

        # To be testing a bit easier, we drop all the irrelevant keys
        for k1, k2 in [('stations', 'route-red'), ('stations', 'route-blue'),
                       ('teams', 'route-red'), ('teams', 'route-blue')]:
            for obj in result_data[k1][k2]:
                drop_all_except(obj, 'name')

        expected = {
            'stations': {
                'route-red': [
                    {'name': 'station-red'},
                    {'name': 'station-start'},
                    {'name': 'station-end'},
                ],
                'route-blue': [
                    {'name': 'station-blue'},
                    {'name': 'station-start'},
                    {'name': 'station-end'},
                ],
            },
            'teams': {
                'route-red': [
                    {'name': 'team-red'}
                ],
                'route-blue': [
                    {'name': 'team-blue'}
                ],
            }
        }
        self.assertCountEqual(result_data['stations']['route-red'],
                              expected['stations']['route-red'])
        self.assertCountEqual(result_data['stations']['route-blue'],
                              expected['stations']['route-blue'])
        self.assertCountEqual(result_data['teams']['route-red'],
                              expected['teams']['route-red'])
        self.assertCountEqual(result_data['teams']['route-blue'],
                              expected['teams']['route-blue'])
