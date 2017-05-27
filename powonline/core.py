from enum import Enum

class TeamState(Enum):
    UNKNOWN = 'unknown'
    ARRIVED = 'arrived'
    FINISHED = 'finished'


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


def advance(team_name, station_name):
    return TeamState.ARRIVED


USER_STATION_MAP = {}
TEAM_ROUTE_MAP = {}
USER_ROLES = {}
ROUTE_STATION_MAP = {}
TEAM_STATION_MAP = {}
