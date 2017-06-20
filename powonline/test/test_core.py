import unittest

from powonline import core
from powonline import model


class CommonTest(unittest.TestCase):

    def setUp(self):
        from sqlalchemy.orm import sessionmaker, scoped_session
        Session = scoped_session(sessionmaker(bind=model.ENGINE))
        self.session = Session()

        self._route_blue = core.Route.create_new(
            self.session, {'name': 'route-blue'})
        self._route_red = core.Route.create_new(
            self.session, {'name': 'route-red'})
        self._station_start = core.Station.create_new(
            self.session, {'name': 'station-start'})
        self._station_blue = core.Station.create_new(
            self.session, {'name': 'station-blue'})
        self._station_red = core.Station.create_new(
            self.session, {'name': 'station-red'})
        self._station_end = core.Station.create_new(
            self.session, {'name': 'station-end'})
        self._team_blue = core.Team.create_new(
            self.session, {'name': 'team-blue', 'route': self._route_blue})
        self._team_red = core.Team.create_new(
            self.session, {'name': 'team-red', 'route': self._route_red})
        self._team_without_route = core.Team.create_new(
            self.session, {'name': 'team-without-route'})
        self._route_blue.stations.add(self._station_start)
        self._route_blue.stations.add(self._station_blue)
        self._route_blue.stations.add(self._station_end)
        self._route_red.stations.add(self._station_start)
        self._route_red.stations.add(self._station_red)
        self._route_red.stations.add(self._station_end)
        # TODO core.ROUTE_STATION_MAP.update({
        # TODO     'station-red': {'route-red'},
        # TODO     'station-start': {'route-blue', 'route-red'},
        # TODO     'station-end': {'route-blue', 'route-red'},
        # TODO })
        # TODO core.TEAM_STATION_MAP.update({
        # TODO     'team-blue': {'station-start': {'state': core.TeamState.ARRIVED}},
        # TODO     'team-red': {'station-start': {'state': core.TeamState.FINISHED},
        # TODO                  'station-red': {'state': core.TeamState.ARRIVED}},
        # TODO })
        # TODO core.USER_ROLES.update({
        # TODO     'user1': {'role1'}
        # TODO })

    def tearDown(self):
        core.USER_ROLES.clear()
        self.session.query(model.Station).delete()
        self.session.query(model.Team).delete()
        self.session.query(model.Route).delete()
        core.TEAM_ROUTE_MAP.clear()
        core.ROUTE_STATION_MAP.clear()
        core.TEAM_STATION_MAP.clear()
        self.session.rollback()


class TestCore(CommonTest):

    @unittest.skip('foo')  # TODO
    def test_get_assignments(self):
        result = core.get_assignments()
        expected = {
            'stations': {
                'route-blue': {self._station_start, self._station_blue, self._station_end},
                'route-red': {self._station_start, self._station_red, self._station_end},
            },
            'teams': {
                'route-blue': {self._team_blue},
                'route-red': {self._team_red},
            }
        }
        self.assertEqual(result, expected)


class TestTeam(CommonTest):

    @unittest.skip('foo')  # TODO
    def test_all(self):
        result = set(core.Team.all())
        expected = {
            self._team_blue,
            self._team_red,
            self._team_without_route,
        }
        self.assertEqual(result, expected)

    @unittest.skip('foo')  # TODO
    def test_quickfilter_without_route(self):
        result = set(core.Team.quickfilter_without_route())
        expected = {self._team_without_route}
        self.assertEqual(result, expected)

    @unittest.skip('foo')  # TODO
    def test_assigned_to_route(self):
        result = set(core.Team.assigned_to_route('route-blue'))
        expected = {self._team_blue}
        self.assertEqual(result, expected)

    @unittest.skip('foo')  # TODO
    def test_create_new(self):
        result = core.Team.create_new({'name': 'foo'})
        self.assertEqual(result.name, 'foo')
        self.assertEqual(len(set(core.Team.all())), 4)
        self.assertIn(result, set(core.Team.all()))

    @unittest.skip('foo')  # TODO
    def test_upsert(self):
        result = core.Team.upsert('team-red', {'name': 'foo', 'contact': 'bar'})
        result.update.assert_called_with(name='foo', contact='bar')

    @unittest.skip('foo')  # TODO
    def test_delete(self):
        result = core.Team.delete('team-red')
        self.assertEqual(len(set(core.Team.all())), 2)
        self.assertIsNone(result)

    @unittest.skip('foo')  # TODO
    def test_get_station_data(self):
        result1 = core.Team.get_station_data('team-red', 'station-start')
        result2 = core.Team.get_station_data('team-blue', 'station-finish')
        expected1 = {'state': core.TeamState.FINISHED}
        expected2 = {'state': core.TeamState.UNKNOWN}
        self.assertEqual(result1, expected1)
        self.assertEqual(result2, expected2)

    @unittest.skip('foo')  # TODO
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

    @unittest.skip('foo')  # TODO
    def test_all(self):
        result = set(core.Station.all())
        expected = {
            self._station_start,
            self._station_blue,
            self._station_red,
            self._station_end,
        }
        self.assertEqual(result, expected)

    @unittest.skip('foo')  # TODO
    def test_create_new(self):
        result = core.Station.create_new({'name': 'foo'})
        self.assertEqual(result.name, 'foo')
        self.assertEqual(len(set(core.Station.all())), 5)
        self.assertIn(result, set(core.Station.all()))

    @unittest.skip('foo')  # TODO
    def test_upsert(self):
        result = core.Station.upsert('station-red',
                                     {'name': 'foo', 'contact': 'bar'})
        result.update.assert_called_with(name='foo', contact='bar')

    @unittest.skip('foo')  # TODO
    def test_delete(self):
        result = core.Station.delete('station-red')
        self.assertEqual(len(set(core.Station.all())), 3)
        self.assertIsNone(result)

    @unittest.skip('foo')  # TODO
    def test_assign_user(self):
        result = core.Station.accessible_by('user1')
        self.assertEqual(result, set())
        result = core.Station.assign_user('station-red', 'user1')
        self.assertTrue(result)
        result = core.Station.accessible_by('user1')
        self.assertEqual(result, {self._station_red.name})

    @unittest.skip('foo')  # TODO
    def test_team_states(self):
        result = core.Station.team_states(self._station_start.name)
        expected = [('team-blue', core.TeamState.ARRIVED),
                    ('team-red', core.TeamState.FINISHED)]
        self.assertCountEqual(result, expected)


class TestRoute(CommonTest):

    def test_all(self):
        result = set(core.Route.all(self.session))
        expected = {
            self._route_blue,
            self._route_red,
        }
        self.assertEqual(result, expected)

    def test_create_new(self):
        result = core.Route.create_new(self.session, {'name': 'foo'})
        stored_data = set(core.Route.all(self.session))
        self.assertEqual(result.name, 'foo')
        self.assertEqual(len(stored_data), 3)
        self.assertIn(result, set(stored_data))

    def test_upsert(self):
        core.Route.upsert(
            self.session, 'route-red', {'name': 'foo'})
        result = core.Route.upsert(
            self.session, 'foo', {'name': 'bar'})
        stored_data = set(core.Route.all(self.session))
        self.assertEqual(result.name, 'bar')
        self.assertEqual(len(stored_data), 2)
        self.assertIn(result, set(stored_data))

    def test_delete(self):
        result = core.Route.delete(self.session, 'route-red')
        self.assertEqual(len(set(core.Route.all(self.session))), 1)
        self.assertIsNone(result)

    def test_assign_team(self):
        result = core.Route.assign_team(
            self.session, 'route-red', 'team-without-route')
        self.assertTrue(result)
        result = set(core.Team.assigned_to_route(self.session, 'route-red'))
        self.assertIn(self._team_without_route, result)

    def test_unassign_team(self):
        result = core.Route.unassign_team(
            self.session, 'route-red', 'team-red')
        self.assertTrue(result)
        result = set(core.Team.assigned_to_route(self.session, 'route-red'))
        self.assertNotIn(self._team_red, result)

    def test_assign_station(self):
        result = core.Route.assign_station(self.session,
                                           'route-red', 'station-blue')
        self.assertTrue(result)
        result = set(core.Station.assigned_to_route(self.session, 'route-red'))
        self.assertIn(self._station_blue, result)

    def test_unassign_station(self):
        result = core.Route.unassign_station(self.session,
                                             'route-red', 'station-red')
        self.assertTrue(result)
        result = set(core.Station.assigned_to_route(self.session, 'route-red'))
        self.assertNotIn(self._station_red, result)


class TestUser(CommonTest):

    @unittest.skip('foo')  # TODO
    def test_assign_role(self):
        core.User.assign_role('user1', 'role2')
        result = core.User.roles('user1')
        self.assertIn('role2', result)

    @unittest.skip('foo')  # TODO
    def test_unassign_role(self):
        core.User.unassign_role('user1', 'role1')
        result = core.User.roles('user1')
        self.assertNotIn('role1', result)
