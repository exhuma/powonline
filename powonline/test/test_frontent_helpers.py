"""
This module contains tests for features implemented mainly for helping the vuejs
based frontens.
"""
import json

from flask_testing import TestCase

from powonline import core
from powonline.web import make_app
import powonline.model as model


def here(localname):
    from os.path import join, dirname
    return join(dirname(__file__), localname)


class TestFrontendHelpers(TestCase):

    SQLALCHEMY_DATABASE_URI = 'postgresql://exhuma@/powonline_testing'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

    def create_app(self):
        return make_app(TestFrontendHelpers.SQLALCHEMY_DATABASE_URI)

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

    def test_fetch_assignments_core(self):

        result = core.get_assignments(model.DB.session)
        assignments_route_team_r = result['teams']['route-red']
        assignments_route_team_b = result['teams']['route-blue']
        assignments_route_station_r = result['stations']['route-red']
        assignments_route_station_b = result['stations']['route-blue']

        expected_assignments_route_team_r = {'team-red'}
        expected_assignments_route_team_b = {'team-blue'}
        expected_assignments_route_station_r = {
            'station-start', 'station-red', 'station-end'}
        expected_assignments_route_station_b = {
            'station-start', 'station-blue', 'station-end'}

        self.assertCountEqual(assignments_route_team_r,
                              expected_assignments_route_team_r)
        self.assertCountEqual(assignments_route_team_b,
                              expected_assignments_route_team_b)
        self.assertCountEqual(assignments_route_station_r,
                              expected_assignments_route_station_r)
        self.assertCountEqual(assignments_route_station_b,
                              expected_assignments_route_station_b)

    def test_fetch_assignments_api(self):
        result = self.app.get('/assignments')
        result_data = json.loads(result.data.decode(result.charset))

        team_result = result_data['teams']
        self.assertEqual(team_result['route-red'], ['team-red'])
        self.assertEqual(team_result['route-blue'], ['team-blue'])

        station_result = result_data['stations']
        self.assertCountEqual(station_result['route-red'], [
            'station-start', 'station-end', 'station-red'])
        self.assertCountEqual(station_result['route-blue'], [
            'station-start', 'station-end', 'station-blue'])
