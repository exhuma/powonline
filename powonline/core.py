from enum import Enum


class TeamState(Enum):
    UNKNOWN = 'unknown'
    ARRIVED = 'arrived'
    FINISHED = 'finished'


def make_default_team_state():
    return {
        'state': TeamState.UNKNOWN
    }


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


class Team:

    @staticmethod
    def all():
        yield make_dummy_team_dict(name='team2')
        yield make_dummy_team_dict(name='team1')
        yield make_dummy_team_dict(name='team3')

    @staticmethod
    def create_new(data):
        return data

    @staticmethod
    def upsert(name, data):
        return data

    @staticmethod
    def delete(name):
        return None

    @staticmethod
    def get_station_data(team_name, station_name):
        state = TEAM_STATION_MAP.get(team_name, {}).get(station_name, {})
        state = state or make_default_team_state()
        return state

    def advance_on_station(team_name, station_name):
        new_state = TeamState.ARRIVED
        return new_state


class Station:

    @staticmethod
    def all():
        yield make_dummy_station_dict(name='station2')
        yield make_dummy_station_dict(name='station1')
        yield make_dummy_station_dict(name='station3')

    @staticmethod
    def create_new(data):
        return data

    @staticmethod
    def upsert(name, data):
        return data

    @staticmethod
    def delete(name):
        return None

    @staticmethod
    def assign_user(station_name, user_name):
        '''
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        '''
        assigned_station = USER_STATION_MAP.get(user_name)
        if assigned_station:
            return False
        USER_STATION_MAP[user_name] = station_name
        return True

    @staticmethod
    def unassign_user(station_name, user_name):
        if station_name in USER_STATION_MAP:
            del(USER_STATION_MAP[station_name])
        return True


class Route:

    @staticmethod
    def all():
        yield make_dummy_route_dict(name='route2')
        yield make_dummy_route_dict(name='route1')
        yield make_dummy_route_dict(name='route3')

    @staticmethod
    def create_new(data):
        return data

    @staticmethod
    def upsert(name, data):
        return data

    @staticmethod
    def delete(name):
        return None

    @staticmethod
    def assign_team(route_name, team_name):
        assigned_route = TEAM_ROUTE_MAP.get(team_name)
        if assigned_route:
            return False
        TEAM_ROUTE_MAP[team_name] = route_name
        return True

    @staticmethod
    def unassign_team(route_name, team_name):
        if team_name in TEAM_ROUTE_MAP:
            del(TEAM_ROUTE_MAP[team_name])
        return True

    @staticmethod
    def assign_station(route_name, station_name):
        assigned_routes = ROUTE_STATION_MAP.get(station_name, set())
        assigned_routes.add(route_name)
        return True

    @staticmethod
    def unassign_station(route_name, station_name):
        assigned_routes = ROUTE_STATION_MAP.get(station_name, set())
        if route_name in assigned_routes:
            assigned_routes.remove(route_name)
        return True


class User:

    @staticmethod
    def assign_role(user_name, role_name):
        assigned_roles = USER_ROLES.get(user_name, set())
        assigned_roles.add(role_name)
        return True

    @staticmethod
    def unassign_role(user_name, role_name):
        roles = USER_ROLES.get(user_name, set())
        if role_name in roles:
            roles.remove(role_name)
        return True


USER_STATION_MAP = {}
TEAM_ROUTE_MAP = {}
USER_ROLES = {}
ROUTE_STATION_MAP = {}
TEAM_STATION_MAP = {}
