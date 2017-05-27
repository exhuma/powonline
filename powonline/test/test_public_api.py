import json
import unittest

from powonline.web import make_app


def make_dummy_team_dict(**overlay):
    '''
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    '''
    output = {
        'name': 'Example Team',
        'email': 'example@example.com',
        'order': None,
        'cancelled': False,
        'contact': 'John Doe',
        'phone': '1234',
        'comments': '',
        'is_confirmed': True,
        'confirmation_key': 'abc',
        'accepted': True,
        'completed': False,
        'inserted': '2017-01-01',
        'updated': '2017-01-02',
        'num_vegetarians': 3,
        'num_participants': 10,
        'planned_start_time': '2017-02-01 12:00',
        'effective_start_time': '2017-02-01 12:10',
        'finish_time': '2017-02-01 14:00',
    }
    output.update(**overlay)
    return output


def make_dummy_station_dict(**overlay):
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
    return output


def make_dummy_route_dict(**overlay):
    '''
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    '''
    output = {
        'name': 'Example Route',
    }
    output.update(**overlay)
    return output


class TestPublicAPIAsManager(unittest.TestCase):

    def setUp(self):
        self.app_object = make_app()
        self.app_object.config['TESTING'] = True
        self.app = self.app_object.test_client()
        self.maxDiff = None

    def test_fetch_list_of_teams(self):
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
        self.skipTest('TODO')

    def test_create_team(self):
        self.skipTest('TODO')

    def test_create_station(self):
        self.skipTest('TODO')

    def test_create_route(self):
        self.skipTest('TODO')

    def test_delete_team(self):
        self.skipTest('TODO')

    def test_delete_station(self):
        self.skipTest('TODO')

    def test_delete_route(self):
        self.skipTest('TODO')

    def assign_user_to_station(self):
        self.skipTest('TODO')

    def assign_user_to_two_stations(self):
        # should fail: integrity error
        self.skipTest('TODO')

    def unassign_user_from_station(self):
        self.skipTest('TODO')

    def assign_team_to_route(self):
        self.skipTest('TODO')

    def assign_team_to_two_routes(self):
        # should fail
        self.skipTest('TODO')

    def unassign_team_from_route(self):
        self.skipTest('TODO')

    def assign_role_to_user(self):
        self.skipTest('TODO')

    def unassign_role_from_user(self):
        self.skipTest('TODO')

    def assign_station_to_route(self):
        self.skipTest('TODO')

    def assign_station_to_two_routes(self):
        # should *pass*. A station can be on multiple routes!
        self.skipTest('TODO')

    def unassign_station_from_route(self):
        self.skipTest('TODO')

    def advance_team_state(self):
        self.skipTest('TODO')


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

    def assign_user_to_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_user_to_two_stations(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_user_from_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_team_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_team_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_team_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_role_to_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_role_from_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_station_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_station_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_station_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def advance_team_state(self):
        self.skipTest('TODO')

    def advance_team_state_on_other_stations(self):
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

    def assign_user_to_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_user_to_two_stations(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_user_from_station(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_team_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_team_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_team_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_role_to_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_role_from_user(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_station_to_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def assign_station_to_two_routes(self):
        # should fail: access denied
        self.skipTest('TODO')

    def unassign_station_from_route(self):
        # should fail: access denied
        self.skipTest('TODO')

    def advance_team_state(self):
        # should fail: access denied
        self.skipTest('TODO')

    def advance_team_state_on_other_stations(self):
        # should fail: access denied
        self.skipTest('TODO')
