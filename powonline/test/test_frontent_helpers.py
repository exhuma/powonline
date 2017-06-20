"""
This module contains tests for features implemented mainly for helping the vuejs
based frontens.
"""
import json
import unittest

from powonline import core
from powonline.web import make_app
import powonline.model as model


class TestPublicAPIAsManager(unittest.TestCase):

    def setUp(self):
        self.app_object = make_app()
        self.app_object.config['TESTING'] = True
        self.app = self.app_object.test_client()

        # create entities
        model.DB.create_all()
        self.route1 = core.Route.create_new(self.session, {'name': 'route1'})
        self.route2 = core.Route.create_new(self.session, {'name': 'route2'})
        self.team1 = core.Team.create_new({'name': 'team1'})
        self.team2 = core.Team.create_new({'name': 'team2'})
        self.station1 = core.Station.create_new({'name': 'station1'})
        self.station2 = core.Station.create_new({'name': 'station2'})

        # create assignments
        core.Route.assign_team('route1', 'team1')
        core.Route.assign_team('route1', 'team2')
        core.Route.assign_station('route2', 'station1')
        core.Route.assign_station('route2', 'station2')

        self.maxDiff = None
        self.session.commit()

    def tearDown(self):
        core.ROLES.clear()
        self.session.query(model.Route).delete()
        core.STATIONS.clear()
        core.TEAMS.clear()
        core.USERS.clear()
        core.USER_STATION_MAP.clear()
        core.TEAM_ROUTE_MAP.clear()
        core.USER_ROLES.clear()
        core.ROUTE_STATION_MAP.clear()
        core.TEAM_STATION_MAP.clear()
        self.session.commit()
        self.session.remove()
        model.DB.drop_all()

    def test_fetch_assignments_core(self):

        result = core.get_assignments(self.session)
        assignments_route_team1 = result['teams']['route1']
        assignments_route_team2 = result['teams']['route2']
        assignments_route_station1 = result['stations']['route1']
        assignments_route_station2 = result['stations']['route2']

        expected_assignments_route_team1 = {self.team1, self.team2}
        expected_assignments_route_team2 = set()
        expected_assignments_route_station1 = set()
        expected_assignments_route_station2 = {self.station1, self.station2}

        self.assertCountEqual(assignments_route_team1,
                              expected_assignments_route_team1)
        self.assertCountEqual(assignments_route_team2,
                              expected_assignments_route_team2)
        self.assertCountEqual(assignments_route_station1,
                              expected_assignments_route_station1)
        self.assertCountEqual(assignments_route_station2,
                              expected_assignments_route_station2)

    def test_fetch_assignments_api(self):
        result = self.app.get('/assignments')
        result_data = json.loads(result.data.decode(result.charset))

        team_result = result_data['teams']
        route_1_team_names = [r['name'] for r in team_result['route1']]
        route_2_team_names = [r['name'] for r in team_result['route2']]
        self.assertCountEqual(route_1_team_names, ['team1', 'team2'])
        self.assertCountEqual(route_2_team_names, [])

        station_result = result_data['stations']
        route_1_station_names = [r['name'] for r in station_result['route1']]
        route_2_station_names = [r['name'] for r in station_result['route2']]
        self.assertCountEqual(route_1_station_names, [])
        self.assertCountEqual(route_2_station_names, ['station1', 'station2'])
