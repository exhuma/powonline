from . import model
from .model import TeamState


def get_assignments(session):

    routes = session.query(model.Route)

    output = {
        'teams': {},
        'stations': {},
    }

    for route in routes:
        output['teams'][route.name] = route.teams
        output['stations'][route.name] = route.stations

    return output


def make_default_team_state():
    return {
        'state': TeamState.UNKNOWN
    }


class Team:

    @staticmethod
    def all(session):
        return session.query(model.Team)

    @staticmethod
    def quickfilter_without_route(session):
        return session.query(model.Team).filter(model.Team.route == None)

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
            state = session.merge(state)

        if state.state == TeamState.UNKNOWN:
            state.state = TeamState.ARRIVED
        elif state.state == TeamState.ARRIVED:
            state.state = TeamState.FINISHED
        else:
            state.state = TeamState.UNKNOWN
        return state.state

    @staticmethod
    def stations(session, team_name):
        team = session.query(model.Team).filter_by(name=team_name).one()
        return team.route.stations

class Station:

    @staticmethod
    def all(session):
        return session.query(model.Station).order_by(model.Station.order)

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
    def team_states(session, station_name):
        # TODO this could be improved by just using one query
        station = session.query(model.Station).filter_by(
            name=station_name).one()
        states = session.query(model.TeamStation).filter_by(
            station_name=station_name)
        mapping = {state.team_name: state for state in states}

        for route in station.routes:
            for team in route.teams:
                state = mapping.get(team.name, model.TeamStation(
                    team_name=team.name,
                    station_name=station_name,
                    state=TeamState.UNKNOWN))
                yield (team.name, state.state)

    @staticmethod
    def accessible_by(session, username):
        user = session.query(model.User).filter_by(name=username).one()
        return {station.name for station in user.stations}


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
    def get(session, name):
        return session.query(model.User).filter_by(name=name).one_or_none()

    @staticmethod
    def delete(session, name):
        session.query(model.User).filter_by(name=name).delete()
        return None

    @staticmethod
    def create_new(session, data):
        user = model.User(**data)
        user = session.add(user)
        return user

    @staticmethod
    def all(session):
        return session.query(model.User)

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
        user = session.query(model.User).filter_by(name=user_name).one()
        return user.roles

    @staticmethod
    def assign_station(session, user_name, station_name):
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
    def unassign_station(session, user_name, station_name):
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
    def may_access_station(session, user_name, station_name):
        user = session.query(model.User).filter_by(
            name=user_name).one()
        user_stations = {_.name for _ in user.stations}
        return station_name in user_stations

class Role:

    @staticmethod
    def get(session, name):
        return session.query(model.Role).filter_by(name=name).one_or_none()

    @staticmethod
    def delete(session, name):
        session.query(model.Role).filter_by(name=name).delete()
        return None

    @staticmethod
    def create_new(session, data):
        role = model.Role(**data)
        role = session.add(role)
        return role

    @staticmethod
    def all(session):
        return session.query(model.Role)
