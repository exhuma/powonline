import unittest

from powonline import core

from util import (
    make_dummy_route_dict,
    make_dummy_station_dict,
    make_dummy_team_dict,
)

TEAM_BLUE = make_dummy_team_dict(True, name='team-blue')
TEAM_RED = make_dummy_team_dict(True, name='team-red')
TEAM_WITHOUT_ROUTE = make_dummy_team_dict(True, name='team-without-route')

ROUTE_BLUE = make_dummy_route_dict(True, name='route-blue')
ROUTE_RED = make_dummy_route_dict(True, name='route-red')

STATION_START = make_dummy_station_dict(True, name='station-start')
STATION_BLUE = make_dummy_station_dict(True, name='station-blue')
STATION_RED = make_dummy_station_dict(True, name='station-red')
STATION_END = make_dummy_station_dict(True, name='station-end')


class CommonTest(unittest.TestCase):

    def setUp(self):
        core.ROUTES.update({
            'route-blue': ROUTE_BLUE,
            'route-red': ROUTE_RED,
        })
        core.STATIONS.update({
            'station-start': STATION_START,
            'station-blue': STATION_BLUE,
            'station-red': STATION_RED,
            'station-end': STATION_END,
        })
        core.TEAMS.update({
            'team-blue': TEAM_BLUE,
            'team-red': TEAM_RED,
            'team-without-route': TEAM_WITHOUT_ROUTE,
        })
        core.TEAM_ROUTE_MAP.update({
            'team-blue': 'route-blue',
            'team-red': 'route-red',
        })
        core.ROUTE_STATION_MAP.update({
            'station-blue': {'route-blue'},
            'station-red': {'route-red'},
            'station-start': {'route-blue', 'route-red'},
            'station-end': {'route-blue', 'route-red'},
        })
        core.TEAM_STATION_MAP.update({
            'team-blue': {'station-start': {'state': core.TeamState.ARRIVED}},
            'team-red': {'station-start': {'state': core.TeamState.FINISHED},
                         'station-red': {'state': core.TeamState.ARRIVED}},
        })
        core.USER_ROLES.update({
            'user1': {'role1'}
        })

    def tearDown(self):
        core.USER_ROLES.clear()
        core.ROUTES.clear()
        core.STATIONS.clear()
        core.TEAMS.clear()
        core.TEAM_ROUTE_MAP.clear()
        core.ROUTE_STATION_MAP.clear()
        core.TEAM_STATION_MAP.clear()


class TestCore(CommonTest):

    def test_get_assignments(self):
        result = core.get_assignments()
        expected = {
            'stations': {
                'route-blue': {STATION_START, STATION_BLUE, STATION_END},
                'route-red': {STATION_START, STATION_RED, STATION_END},
            },
            'teams': {
                'route-blue': {TEAM_BLUE},
                'route-red': {TEAM_RED},
            }
        }
        self.assertEqual(result, expected)


class TestTeam(CommonTest):

    def test_all(self):
        result = set(core.Team.all())
        expected = {
            TEAM_BLUE,
            TEAM_RED,
            TEAM_WITHOUT_ROUTE,
        }
        self.assertEqual(result, expected)

    def test_quickfilter_without_route(self):
        result = set(core.Team.quickfilter_without_route())
        expected = {TEAM_WITHOUT_ROUTE}
        self.assertEqual(result, expected)

    def test_assigned_to_route(self):
        result = set(core.Team.assigned_to_route('route-blue'))
        expected = {TEAM_BLUE}
        self.assertEqual(result, expected)

    def test_create_new(self):
        result = core.Team.create_new({'name': 'foo'})
        self.assertEqual(result.name, 'foo')
        self.assertEqual(len(set(core.Team.all())), 4)
        self.assertIn(result, set(core.Team.all()))

    def test_upsert(self):
        result = core.Team.upsert('team-red', {'name': 'foo', 'contact': 'bar'})
        result.update.assert_called_with(name='foo', contact='bar')

    def test_delete(self):
        result = core.Team.delete('team-red')
        self.assertEqual(len(set(core.Team.all())), 2)
        self.assertIsNone(result)

    def test_get_station_data(self):
        result1 = core.Team.get_station_data('team-red', 'station-start')
        result2 = core.Team.get_station_data('team-blue', 'station-finish')
        expected1 = {'state': core.TeamState.FINISHED}
        expected2 = {'state': core.TeamState.UNKNOWN}
        self.assertEqual(result1, expected1)
        self.assertEqual(result2, expected2)

    def test_advance_on_station(self):
        new_state = core.Team.advance_on_station('team-red', 'station_start')
        self.assertEqual(new_state, core.TeamState.ARRIVED)
        new_state = core.Team.advance_on_station('team-red', 'station_start')
        self.assertEqual(new_state, core.TeamState.FINISHED)
        new_state = core.Team.advance_on_station('team-red', 'station_start')
        self.assertEqual(new_state, core.TeamState.UNKNOWN)
        new_state = core.Team.advance_on_station('team-red', 'station_start')
        self.assertEqual(new_state, core.TeamState.ARRIVED)


class TestStation(CommonTest):

    def test_all(self):
        result = set(core.Station.all())
        expected = {
            STATION_START,
            STATION_BLUE,
            STATION_RED,
            STATION_END,
        }
        self.assertEqual(result, expected)

    def test_create_new(self):
        result = core.Station.create_new({'name': 'foo'})
        self.assertEqual(result.name, 'foo')
        self.assertEqual(len(set(core.Station.all())), 5)
        self.assertIn(result, set(core.Station.all()))

    def test_upsert(self):
        result = core.Station.upsert('station-red',
                                     {'name': 'foo', 'contact': 'bar'})
        result.update.assert_called_with(name='foo', contact='bar')

    def test_delete(self):
        result = core.Station.delete('station-red')
        self.assertEqual(len(set(core.Station.all())), 3)
        self.assertIsNone(result)

    def test_assign_user(self):
        result = core.Station.accessible_by('user1')
        self.assertEqual(result, set())
        result = core.Station.assign_user('station-red', 'user1')
        self.assertTrue(result)
        result = core.Station.accessible_by('user1')
        self.assertEqual(result, {STATION_RED.name})

    def test_team_states(self):
        result = core.Station.team_states(STATION_START.name)
        expected = [('team-blue', core.TeamState.ARRIVED),
                    ('team-red', core.TeamState.FINISHED)]
        self.assertCountEqual(result, expected)


class TestRoute(CommonTest):

    def test_all(self):
        result = set(core.Route.all())
        expected = {
            ROUTE_BLUE,
            ROUTE_RED,
        }
        self.assertEqual(result, expected)

    def test_create_new(self):
        result = core.Route.create_new({'name': 'foo'})
        self.assertEqual(result.name, 'foo')
        self.assertEqual(len(set(core.Route.all())), 3)
        self.assertIn(result, set(core.Route.all()))

    def test_upsert(self):
        result = core.Route.upsert('route-red',
                                   {'name': 'foo', 'contact': 'bar'})
        result.update.assert_called_with(name='foo', contact='bar')

    def test_delete(self):
        result = core.Route.delete('route-red')
        self.assertEqual(len(set(core.Route.all())), 1)
        self.assertIsNone(result)

    def test_assign_team(self):
        result = core.Route.assign_team('route-red', 'team-without-route')
        self.assertTrue(result)
        result = set(core.Team.assigned_to_route('route-red'))
        self.assertIn(TEAM_WITHOUT_ROUTE, result)

    def test_unassign_team(self):
        result = core.Route.unassign_team('route-red', 'team-red')
        self.assertTrue(result)
        result = set(core.Team.assigned_to_route('route-red'))
        self.assertNotIn(TEAM_RED, result)

    def test_assign_station(self):
        result = core.Route.assign_station('route-red', 'station-blue')
        self.assertTrue(result)
        result = set(core.Station.assigned_to_route('route-red'))
        self.assertIn(STATION_BLUE, result)

    def test_unassign_station(self):
        result = core.Route.unassign_station('route-red', 'station-red')
        self.assertTrue(result)
        result = set(core.Station.assigned_to_route('route-red'))
        self.assertNotIn(STATION_RED, result)


class TestUser(CommonTest):

    def test_assign_role(self):
        core.User.assign_role('user1', 'role2')
        result = core.User.roles('user1')
        self.assertIn('role2', result)

    def test_unassign_role(self):
        core.User.unassign_role('user1', 'role1')
        result = core.User.roles('user1')
        self.assertNotIn('role1', result)
