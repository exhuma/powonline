from datetime import datetime
from unittest.mock import create_autospec, patch
import json
import unittest

from powonline.web import make_app
import powonline.model as mdl


def make_dummy_team_dict(as_mock=False, **overlay):
    '''
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    '''
    tstamp = (datetime(2017, 1, 1, 10, 0) if as_mock
              else '2017-01-01T10:00:00+00:00')
    output = {
        'name': 'Example Team',
        'email': 'example@example.com',
        'order': 0,
        'cancelled': False,
        'contact': 'John Doe',
        'phone': '1234',
        'comments': '',
        'is_confirmed': True,
        'confirmation_key': 'abc',
        'accepted': True,
        'completed': False,
        'inserted': tstamp,
        'updated': None,
        'num_vegetarians': 3,
        'num_participants': 10,
        'planned_start_time': None,
        'effective_start_time': None,
        'finish_time': None,
    }
    output.update(**overlay)
    if as_mock:
        mock = create_autospec(mdl.Team)
        for k, v in output.items():
            setattr(mock, k, v)
        return mock
    else:
        return output


def make_dummy_station_dict(as_mock=False, **overlay):
    '''
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    '''
    output = {
        'name': 'Example Station',
        'contact': 'Example Contact',
        'phone': '12345',
        'is_start': False,
        'is_end': False,
    }
    output.update(**overlay)
    if as_mock:
        mock = create_autospec(mdl.Station)
        for k, v in output.items():
            setattr(mock, k, v)
        return mock
    else:
        return output


def make_dummy_route_dict(as_mock=False, **overlay):
    '''
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    '''
    output = {
        'name': 'Example Route',
    }
    output.update(**overlay)
    if as_mock:
        mock = create_autospec(mdl.Route)
        for k, v in output.items():
            setattr(mock, k, v)
        return mock
    else:
        return output


class TestPublicAPIAsManager(unittest.TestCase):

    def setUp(self):
        self.app_object = make_app()
        self.app_object.config['TESTING'] = True
        self.app = self.app_object.test_client()
        self.maxDiff = None

    def tearDown(self):
        from powonline import core
        core.USER_STATION_MAP.clear()
        core.TEAM_ROUTE_MAP.clear()

    def test_fetch_list_of_teams(self):
        with patch('powonline.resources.core') as _core:
            _core.Team.all.return_value = [
                make_dummy_team_dict(as_mock=True, name='team1'),
                make_dummy_team_dict(as_mock=True, name='team2'),
                make_dummy_team_dict(as_mock=True, name='team3'),
            ]
            response = self.app.get('/team')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, 'application/json')
        response_text = response.data.decode(response.charset)
        data = json.loads(response_text)
        items = data['items']
        expected = [
            make_dummy_team_dict(name='team1'),
            make_dummy_team_dict(name='team2'),
            make_dummy_team_dict(name='team3'),
        ]
        self.assertCountEqual(items, expected)

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
            response = self.app.put('/route/old-route',
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
        simpleuser = {'name': 'example-user'}
        response = self.app.post('/station/example-station/users',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleuser))
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_user_to_two_stations(self):
        simpleuser = {'name': 'example-user'}
        response = self.app.post('/station/example-station-1/users',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleuser))
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post('/station/example-station-2/users',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleuser))
        self.assertEqual(response.status_code, 400, response.data)

    def test_unassign_user_from_station(self):
        response = self.app.delete('/station/example-station/users/some-user')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_team_to_route(self):
        simpleteam = {'name': 'example-team'}
        response = self.app.post('/route/example-route/teams',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleteam))
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_team_to_two_routes(self):
        simpleteam = {'name': 'example-team'}
        response = self.app.post('/route/example-route-1/teams',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleteam))
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post('/route/example-route-2/teams',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simpleteam))
        self.assertEqual(response.status_code, 400, response.data)

    def test_unassign_team_from_route(self):
        response = self.app.delete('/route/example-route/teams/someteam')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_role_to_user(self):
        simplerole = {'name': 'example-role'}
        response = self.app.post('/user/example-user/roles',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplerole))
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_role_from_user(self):
        response = self.app.delete('/user/example-user/roles/somerole')
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_station_to_route(self):
        simplestation = {'name': 'example-station'}
        response = self.app.post('/route/example-route/stations',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplestation))
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_station_to_two_routes(self):
        # should *pass*. A station can be on multiple routes!
        simplestation = {'name': 'example-station'}
        response = self.app.post('/route/example-route-1/stations',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplestation))
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post('/route/example-route-2/stations',
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(simplestation))
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_station_from_route(self):
        response = self.app.delete('/route/example-route/stations/somestation')
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
                'station_name': 'somestation',
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
