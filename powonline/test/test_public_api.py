from configparser import ConfigParser
from textwrap import dedent
from unittest.mock import patch
import json
import unittest

from flask_testing import TestCase

from powonline.model import DB
from powonline.web import make_app
import powonline.core as core

from util import (
    make_dummy_route_dict,
    make_dummy_station_dict,
    make_dummy_team_dict,
)


def here(localname):
    from os.path import join, dirname
    return join(dirname(__file__), localname)


class TestPublicAPIAsManager(TestCase):

    SQLALCHEMY_DATABASE_URI = 'postgresql://exhuma@/powonline_testing'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

    def create_app(self):
        config = ConfigParser()
        config.read_string(dedent(
            '''\
            [db]
            dsn = %s
            ''' % (
                TestPublicAPIAsManager.SQLALCHEMY_DATABASE_URI,
            )))
        return make_app(config)

    def setUp(self):
        self.app = self.client  # <-- avoiding unrelated diffs for now.
                                #     Can be removed in a later commit
        DB.create_all()

        with open(here('seed.sql')) as seed:
            DB.session.execute(seed.read())
            DB.session.commit()

        self.maxDiff = None

    def tearDown(self):
        DB.session.remove()
        DB.drop_all()

    def test_fetch_list_of_teams_all(self):
        with patch('powonline.resources.core') as _core:
            _core.Team.all.return_value = []
            self.app.get('/team')
            _core.Team.all.assert_called_with(DB.session)

    def test_fetch_list_of_teams_by_route(self):
        with patch('powonline.resources.core') as _core:
            _core.Team.assigned_to_route.return_value = []
            self.app.get('/team?assigned_route=foo')
            _core.Team.assigned_to_route.assert_called_with(DB.session, 'foo')

    def test_fetch_list_of_teams_quickfilter_without_route(self):
        with patch('powonline.resources.core') as _core:
            _core.Team.quickfilter_without_route.return_value = []
            self.app.get('/team?quickfilter=without_route')
            _core.Team.quickfilter_without_route.assert_called_with(DB.session)

    def test_fetch_list_of_stations(self):
        with patch('powonline.resources.core') as _core:
            _core.Station.all.return_value = [
                make_dummy_station_dict(as_mock=True, name='station1'),
                make_dummy_station_dict(as_mock=True, name='station2'),
                make_dummy_station_dict(as_mock=True, name='station3'),
            ]
            response = self.app.get('/station')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        items = data['items']
        expected = [
            make_dummy_station_dict(name='station1'),
            make_dummy_station_dict(name='station2'),
            make_dummy_station_dict(name='station3'),
        ]
        self.assertCountEqual(items, expected)

    def test_fetch_list_of_routes(self):
        with patch('powonline.resources.core') as _core:
            _core.Route.all.return_value = [
                make_dummy_route_dict(as_mock=True, name='route1'),
                make_dummy_route_dict(as_mock=True, name='route2'),
                make_dummy_route_dict(as_mock=True, name='route3'),
            ]
            response = self.app.get('/route')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        items = data['items']
        expected = [
            make_dummy_route_dict(name='route1'),
            make_dummy_route_dict(name='route2'),
            make_dummy_route_dict(name='route3'),
        ]
        self.assertCountEqual(items, expected)

    def test_update_team(self):
        replacement_team = make_dummy_team_dict(
            name='foo',
            contact='new-contact')

        response = self.app.put('/team/old-team',
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps(replacement_team))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_team_dict(
            name='foo',
            contact='new-contact')
        self.assertEqual(data, expected)

    def test_update_own_station(self):
        replacement_station = make_dummy_station_dict(
            name='foo',
            contact='new-contact')

        response = self.app.put('/station/old-station',
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps(replacement_station))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_station_dict(
            name='foo',
            contact='new-contact')
        self.assertEqual(data, expected)

    def test_update_other_station(self):
        replacement_station = make_dummy_station_dict(
            name='foo',
            contact='new-contact')

        response = self.app.put('/station/not-my-station',
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps(replacement_station))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_station_dict(
            name='foo',
            contact='new-contact')
        self.assertEqual(data, expected)

    def test_update_route(self):
        replacement_route = make_dummy_route_dict(
            name='foo',
            contact='new-contact')

        with patch('powonline.resources.core') as _core:
            mocked_route = make_dummy_route_dict(
                as_mock=True,
                name='foo',
                contact='new-contact')
            _core.Route.upsert.return_value = mocked_route
            response = self.app.put(
                '/route/old-route',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(replacement_route))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_route_dict(name='foo')
        self.assertEqual(data, expected)

    def test_create_team(self):
        new_team = make_dummy_team_dict(
            name='foo',
            contact='new-contact')

        response = self.app.post('/team',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(new_team))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_team_dict(
            name='foo',
            contact='new-contact')
        self.assertEqual(data, expected)

    def test_create_station(self):
        new_station = make_dummy_station_dict(
            name='foo',
            contact='new-contact')

        response = self.app.post('/station',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(new_station))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_station_dict(
            name='foo',
            contact='new-contact')
        self.assertEqual(data, expected)

    def test_create_route(self):
        new_route = make_dummy_route_dict(
            name='foo',
            contact='new-contact')

        response = self.app.post('/route',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(new_route))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        expected = make_dummy_route_dict(name='foo')
        self.assertEqual(data, expected)

    def test_delete_team(self):
        response = self.app.delete('/team/example-team')
        self.assertEqual(response.status_code, 204, response.data)

    def test_delete_station(self):
        response = self.app.delete('/station/example-station')
        self.assertEqual(response.status_code, 204, response.data)

    def test_delete_route(self):
        response = self.app.delete('/route/example-route')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_user_to_station(self):
        simpleuser = {'name': 'john'}
        response = self.app.post('/station/station-red/users',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleuser))
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_user_to_two_stations(self):
        simpleuser = {'name': 'john'}
        response = self.app.post('/station/station-red/users',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleuser))
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post('/station/station-blue/users',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleuser))
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_user_from_station(self):
        response = self.app.delete('/station/station-red/users/user-red')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_team_to_route(self):
        simpleteam = {'name': 'team-without-route'}
        response = self.app.post('/route/route-red/teams',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleteam))
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_team_to_two_routes(self):
        simpleteam = {'name': 'team-without-route'}
        response = self.app.post('/route/route-red/teams',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleteam))
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post('/route/route-blue/teams',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleteam))
        self.assertEqual(response.status_code, 400, response.data)

    def test_unassign_team_from_route(self):
        response = self.app.delete('/route/route-red/teams/team-red')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_role_to_user(self):
        simplerole = {'name': 'a-role'}
        response = self.app.post('/user/jane/roles',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplerole))
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_role_from_user(self):
        response = self.app.delete('/user/john/roles/a-role')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_station_to_route(self):
        simplestation = {'name': 'station-red'}
        response = self.app.post('/route/route-red/stations',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplestation))
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_station_to_two_routes(self):
        # should *pass*. A station can be on multiple routes!
        simplestation = {'name': 'station-start'}
        response = self.app.post('/route/route-red/stations',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplestation))
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post('/route/route-blue/stations',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplestation))
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_station_from_route(self):
        response = self.app.delete('/route/route-red/stations/station-red')
        self.assertEqual(response.status_code, 204, response.data)

    def test_show_team_station_state(self):
        response = self.app.get('/team/example-team/stations/somestation')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        self.assertEqual(data['state'], 'unknown')

    def test_show_team_station_state_inverse(self):
        '''
        Team and Station should be interchangeable in the URL
        '''
        response = self.app.get('/station/example-station/teams/someteam')
        self.assertEqual(response.status_code, 200, response.data)

    def test_advance_team_state(self):
        simplejob = {
            'action': 'advance',
            'args': {
                'station_name': 'station-red',
                'team_name': 'someteam',
            }
        }
        response = self.app.post('/job',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplejob))
        self.assertEqual(response.status_code, 200, response.data)
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        result = data['result']
        self.assertEqual(result, {'state': 'arrived'})

    def test_dashboard(self):
        with patch('powonline.resources.core') as _core:
            _core.Station.team_states.return_value = [
                ('team1', core.TeamState.ARRIVED),
                ('team2', core.TeamState.UNKNOWN),
            ]
            result = self.app.get('/station/station-1/dashboard')
            data = json.loads(result.data.decode(result.charset))
            testable = {
                (row['score'], row['team'], row['state'])
                for row in data
            }
            expected = {
                (0, 'team1', 'arrived'),
                (0, 'team2', 'unknown'),
            }
            self.assertEqual(testable, expected)


class TestPublicAPIAsStationManager(unittest.TestCase):

    def test_fetch_list_of_teams(self):
        self.skipTest('TODO')

    def test_fetch_list_of_stations(self):
        self.skipTest('TODO')

    def test_fetch_list_of_routes(self):
        self.skipTest('TODO')

    def test_update_team(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_update_own_station(self):
        self.skipTest('TODO')

    def test_update_other_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_update_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_create_team(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_create_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_create_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_delete_team(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_delete_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_delete_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_user_to_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_user_to_two_stations(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_user_from_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_team_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_team_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_team_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_role_to_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_role_from_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_station_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_station_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_station_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_advance_team_state(self):
        self.skipTest('TODO')

    def test_advance_team_state_on_other_stations(self):
        # should fail: access denied
        self.skipTest('TODO')


class TestPublicAPIAsAnonymous(unittest.TestCase):

    def test_fetch_list_of_teams(self):
        self.skipTest('TODO')

    def test_fetch_list_of_stations(self):
        self.skipTest('TODO')

    def test_fetch_list_of_routes(self):
        self.skipTest('TODO')

    def test_update_team(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_update_own_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_update_other_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_update_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_create_team(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_create_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_create_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_delete_team(self):
        # should fail
        self.skipTest('TODO')

    def test_delete_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_delete_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_user_to_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_user_to_two_stations(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_user_from_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_team_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_team_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_team_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_role_to_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_role_from_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_station_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_assign_station_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_unassign_station_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_advance_team_state(self):
        # should fail: access denied
        self.skipTest('TODO')

    def test_advance_team_state_on_other_stations(self):
        # should fail: access denied
        self.skipTest('TODO')
