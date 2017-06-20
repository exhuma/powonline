from . import model
from .model import TeamState

# fake in-memory storage
ROLES = {}  # set of role names
USERS = {}  # set of user names
TEAMS = {}  # key: team-name, value: Team object

USER_STATION_MAP = {}  # key: user-name, value: station-name
TEAM_ROUTE_MAP = {}  # key: team-name, value: route-name
USER_ROLES = {}  # key: user-name, value: role-name
ROUTE_STATION_MAP = {}  # key: station-name, value: set of route-names
TEAM_STATION_MAP = {}  # key: team-name, value: object(key: station-name, value: state-object)


def get_assignments(session):
    route_teams = {route.name: set() for route in Route.all(session)}
    for team_name, route_name in TEAM_ROUTE_MAP.items():
        route_teams[route_name].add(TEAMS[team_name])

    route_stations = {route.name: set() for route in Route.all(session)}
    for station_name, route_names in ROUTE_STATION_MAP.items():
        for route_name in route_names:
            route_stations[route_name].add(STATIONS[station_name])

    return {
        'teams': route_teams,
        'stations': route_stations
    }


def make_default_team_state():
    return {
        'state': TeamState.UNKNOWN
    }


class Team:

    @staticmethod
    def all():
        for team in TEAMS.values():
            yield team

    @staticmethod
    def quickfilter_without_route():
        assigned = set(TEAM_ROUTE_MAP.keys())
        for team in Team.all():
            if team.name not in assigned:
                yield team

    @staticmethod
    def assigned_to_route(session, route_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one()
        return route.teams

    @staticmethod
    def create_new(session, data):
        team = model.Team(**data)
        team = session.merge(team)
        return team

    @staticmethod
    def upsert(name, data):
        team = TEAMS.get(name, model.Team())
        team.update(**data)
        return team

    @staticmethod
    def delete(name):
        if name in TEAMS:
            del(TEAMS[name])
        return None

    @staticmethod
    def get_station_data(team_name, station_name):
        state = TEAM_STATION_MAP.get(team_name, {}).get(station_name, {})
        state = state or make_default_team_state()
        return state

    def advance_on_station(team_name, station_name):
        state = TEAM_STATION_MAP.get(team_name, {}).setdefault(
            station_name, make_default_team_state())
        if state['state'] == TeamState.UNKNOWN:
            state['state'] = TeamState.ARRIVED
        elif state['state'] == TeamState.ARRIVED:
            state['state'] = TeamState.FINISHED
        else:
            state['state'] = TeamState.UNKNOWN
        return state['state']


class Station:

    @staticmethod
    def all(session):
        return session.query(model.Station)

    @staticmethod
    def create_new(session, data):
        station = model.Station(**data)
        station = session.merge(station)
        return station

    @staticmethod
    def upsert(name, data):
        station = STATIONS.get(name, model.Station())
        station.update(**data)
        return station

    @staticmethod
    def delete(name):
        if name in STATIONS:
            del(STATIONS[name])
        return None

    @staticmethod
    def assigned_to_route(session, route_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one_or_none()
        return route.stations

    @staticmethod
    def assign_user(station_name, user_name):
        '''
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        '''
        if user_name in USER_STATION_MAP:
            return False
        assigned_stations = USER_STATION_MAP.setdefault(user_name, set())
        assigned_stations.add(station_name)
        return True

    @staticmethod
    def unassign_user(station_name, user_name):
        assigned_stations = USER_STATION_MAP.setdefault(user_name, set())
        if station_name in assigned_stations:
            assigned_stations.remove(station_name)
        return True

    @staticmethod
    def team_states(station_name):
        output = []
        teams = []

        # First look which routes this station is assigned to
        routes = ROUTE_STATION_MAP.setdefault(station_name, [])

        # ... now find all the teams assigned to those routes
        for team_name, team_route in TEAM_ROUTE_MAP.items():
            if team_route in routes:
                teams.append(team_name)

        for team_name in teams:
            team_station = TEAM_STATION_MAP.setdefault(team_name, {})
            state = team_station.setdefault(station_name,
                                            make_default_team_state())
            output.append((team_name, state['state']))

        return output

    @staticmethod
    def accessible_by(username):
        return USER_STATION_MAP.get(username, set())


class Route:

    @staticmethod
    def all(session):
        return session.query(model.Route)

    @staticmethod
    def create_new(session, data):
        route = model.Route(**data)
        route = session.merge(route)
        return route

    @staticmethod
    def upsert(session, name, data):
        old = session.query(model.Route).filter_by(name=name).first()
        if not old:
            old = Route.create_new(session, data)
        for k, v in data.items():
            setattr(old, k, v)
        return old

    @staticmethod
    def delete(session, name):
        session.query(model.Route).filter_by(name=name).delete()
        return None

    @staticmethod
    def assign_team(session, route_name, team_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one()
        team = session.query(model.Team).filter_by(
            name=team_name).one()
        route.teams.add(team)
        return True

    @staticmethod
    def unassign_team(session, route_name, team_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one()
        team = session.query(model.Team).filter_by(
            name=team_name).one()
        route.teams.remove(team)
        return True

    @staticmethod
    def assign_station(session, route_name, station_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one()
        station = session.query(model.Station).filter_by(
            name=station_name).one()
        route.stations.add(station)
        return True

    @staticmethod
    def unassign_station(session, route_name, station_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one()
        station = session.query(model.Station).filter_by(
            name=station_name).one()
        route.stations.remove(station)
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

    @staticmethod
    def roles(user_name):
        return USER_ROLES.get(user_name, set())
