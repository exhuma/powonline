from . import model
from .model import TeamState


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
    def upsert(session, name, data):
        old = session.query(model.Team).filter_by(name=name).first()
        if not old:
            old = Team.create_new(session, data)
        for k, v in data.items():
            setattr(old, k, v)
        return old

    @staticmethod
    def delete(session, name):
        session.query(model.Team).filter_by(name=name).delete()
        return None

    @staticmethod
    def get_station_data(session, team_name, station_name):
        state = session.query(model.TeamStation).filter_by(
            team_name=team_name, station_name=station_name).one_or_none()
        if not state:
            return model.TeamStation(team_name=team_name,
                                     station_name=station_name)
        else:
            return state

    def advance_on_station(session, team_name, station_name):
        state = session.query(model.TeamStation).filter_by(
            team_name=team_name, station_name=station_name).one_or_none()
        if not state:
            state = model.TeamStation(team_name=team_name,
                                      station_name=station_name)

        if state.state == TeamState.UNKNOWN:
            state.state = TeamState.ARRIVED
        elif state.state == TeamState.ARRIVED:
            state.state = TeamState.FINISHED
        else:
            state.state = TeamState.UNKNOWN
        return state.state


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
    def upsert(session, name, data):
        old = session.query(model.Station).filter_by(name=name).first()
        if not old:
            old = Station.create_new(session, data)
        for k, v in data.items():
            setattr(old, k, v)
        return old

    @staticmethod
    def delete(session, name):
        session.query(model.Station).filter_by(name=name).delete()
        return None

    @staticmethod
    def assigned_to_route(session, route_name):
        route = session.query(model.Route).filter_by(
            name=route_name).one_or_none()
        return route.stations

    @staticmethod
    def assign_user(session, station_name, user_name):
        '''
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        '''
        station = session.query(model.Station).filter_by(
            name=station_name).one()
        user = session.query(model.User).filter_by(name=user_name).one()
        station.users.add(user)
        return True

    @staticmethod
    def unassign_user(session, station_name, user_name):
        station = session.query(model.Station).filter_by(
            name=station_name).one()

        found_user = None
        for user in station.users:
            if user.name == user_name:
                found_user = user
                break

        if found_user:
            station.users.remove(found_user)

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
        team = session.query(model.Team).filter_by(
            name=team_name).one()
        if team.route:
            return False  # A team can only be assigned to one route
        route = session.query(model.Route).filter_by(
            name=route_name).one()
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
    def assign_role(session, user_name, role_name):
        user = session.query(model.User).filter_by(name=user_name).one()
        role = session.query(model.Role).filter_by(name=role_name).one()
        user.roles.add(role)
        return True

    @staticmethod
    def unassign_role(session, user_name, role_name):
        user = session.query(model.User).filter_by(name=user_name).one()
        role = session.query(model.Role).filter_by(name=role_name).one_or_none()
        if role:
            user.roles.remove(role)
        return True

    @staticmethod
    def roles(session, user_name):
        raise NotImplementedError('Not yet implemented')
