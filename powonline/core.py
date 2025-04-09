import logging
from datetime import datetime, timezone
from enum import Enum, auto
from os import makedirs
from os.path import basename, dirname, join
from random import SystemRandom
from string import ascii_letters, digits, punctuation
from typing import Generator, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Query, Session, scoped_session

from . import model
from .exc import (
    NoQuestionnaireForStation,
    NoSuchQuestionnaire,
    PowonlineException,
)
from .model import TeamState

LOG = logging.getLogger(__name__)


class StationRelation(Enum):
    """
    A station-relation defines how one station relates to another.
    """

    PREVIOUS = auto()
    NEXT = auto()


def get_assignments(session):
    routes = session.query(model.Route)

    output = {
        "teams": {},
        "stations": {},
    }

    for route in routes:
        output["teams"][route.name] = route.teams
        output["stations"][route.name] = route.stations

    return output


def make_default_team_state():
    return {"state": TeamState.UNKNOWN}


def scoreboard(session):
    teams = session.query(model.Team)
    scores = {}
    for row in teams:
        station_score = sum(state.score for state in row.station_states)
        quest_score = sum(quest.score for quest in row.questionnaire_scores)
        scores[row.name] = sum([station_score, quest_score])
    output = reversed(sorted(scores.items(), key=lambda x: x[1]))
    return output


def questionnaire_scores(
    session: Session,
) -> dict[str, dict[str, dict[str, str | int]]]:
    query: Query[model.TeamQuestionnaire] = session.query(
        model.TeamQuestionnaire
    ).join(model.Questionnaire)
    output: dict[str, dict[str, dict[str, str | int]]] = {}
    for row in query:
        print(row)
        team_name: str = row.team_name  # type: ignore
        questionnaire_name: str = row.questionnaire_name  # type: ignore
        score: int = row.score  # type: ignore
        station = row.questionnaire.station.name
        team_stations = output.setdefault(team_name, {})
        team_stations[station] = {
            "name": questionnaire_name,
            "score": score,
        }
    return output


def add_audit_log(
    session: scoped_session, username: str, type_: model.AuditType, message: str
) -> model.AuditLog:
    entry = model.AuditLog(
        timestamp=datetime.now(timezone.utc),
        username=username,
        type_=type_,
        message=message,
    )
    LOG.debug("New entry on audit-trail: %r", entry)
    session.add(entry)
    return entry


def set_questionnaire_score(
    session: Session, team: str, station: str, score: int
):
    """
    Set the team-score for a questionaire on a given station.
    """
    station_entity = (
        session.query(model.Station).filter_by(name=station).one_or_none()
    )
    if not station_entity:
        raise PowonlineException(f"Station {station} not found")

    if not station_entity.questionnaires:
        raise NoQuestionnaireForStation(station_entity)

    if len(station_entity.questionnaires) > 1:
        raise NoQuestionnaireForStation(
            station_entity, "Multiple questionnaires assigned"
        )

    existing_questionnaire = station_entity.questionnaires[0]
    questionnaire_name = existing_questionnaire.name

    query = session.query(model.TeamQuestionnaire).filter_by(
        team_name=team, questionnaire_name=questionnaire_name
    )
    state = query.one_or_none()
    if not state:
        state = model.TeamQuestionnaire(team, questionnaire_name, score)
        session.add(state)
    old_score = state.score
    state.score = score
    return old_score, score


def global_dashboard(session):
    teams = session.query(model.Team).order_by(model.Team.name)
    stations = session.query(model.Station).order_by(model.Station.name)
    team_names = set()
    station_names = set()
    output = []
    for team in teams:
        team_names.add(team.name)
        team_data = {"stations": [], "team": team.name}
        if team.route:
            reachable_stations = {
                station.name for station in team.route.stations
            }
        else:
            reachable_stations = set()
        for station in stations:
            station_names.add(station.name)
            if station.name in reachable_stations:
                team_states = session.query(model.TeamStation).filter(
                    and_(
                        model.TeamStation.team == team,
                        model.TeamStation.station == station,
                    )
                )
                dbstate = team_states.one_or_none()
                if dbstate:
                    cell_state = dbstate.state
                    cell_score = dbstate.score
                else:
                    cell_state = TeamState.UNKNOWN
                    cell_score = 0
            else:
                cell_state = TeamState.UNREACHABLE
                cell_score = 0
            team_data["stations"].append(
                {"name": station.name, "score": cell_score, "state": cell_state}
            )
        output.append(team_data)
    return output


class Team:
    @staticmethod
    def all(session):
        return session.query(model.Team).order_by(
            model.Team.effective_start_time
        )

    @staticmethod
    def get(session, name):
        return session.query(model.Team).filter_by(name=name).one_or_none()

    @staticmethod
    def quickfilter_without_route(session):
        return session.query(model.Team).filter(model.Team.route == None)

    @staticmethod
    def assigned_to_route(session, route_name):
        route = session.query(model.Route).filter_by(name=route_name).one()
        return route.teams

    @staticmethod
    def create_new(session, data):
        team = model.Team(**data)
        if not data.get("confirmation_key"):
            team.reset_confirmation_key()
        team = session.merge(team)
        return team

    @staticmethod
    def upsert(session, name, data):
        data.pop("inserted", None)
        data.pop("updated", None)
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
        state = (
            session.query(model.TeamStation)
            .filter_by(team_name=team_name, station_name=station_name)
            .one_or_none()
        )
        if not state:
            return model.TeamStation(
                team_name=team_name, station_name=station_name
            )
        else:
            return state

    @staticmethod
    def advance_on_station(session, team_name, station_name):
        state = (
            session.query(model.TeamStation)
            .filter_by(team_name=team_name, station_name=station_name)
            .one_or_none()
        )
        if not state:
            state = model.TeamStation(
                team_name=team_name, station_name=station_name
            )
            state = session.merge(state)
            session.flush()

        if state.state == TeamState.UNKNOWN:
            state.state = TeamState.ARRIVED
            # Teams which arrive at the finish station will have their
            # finish-time set
            if not state.team.finish_time and state.station.is_end:
                state.team.finish_time = func.now()
        elif state.state == TeamState.ARRIVED:
            # Teams which leave the departure station will have their
            # start-time set
            if not state.team.effective_start_time and state.station.is_start:
                state.team.effective_start_time = func.now()
            state.state = TeamState.FINISHED
        else:
            state.state = TeamState.UNKNOWN
        return state.state

    @staticmethod
    def set_station_score(
        session: scoped_session, team_name, station_name, score
    ):
        state = (
            session.query(model.TeamStation)
            .filter_by(team_name=team_name, station_name=station_name)
            .one_or_none()
        )
        if not state:
            state = model.TeamStation(
                team_name=team_name, station_name=station_name
            )
            state = session.merge(state)
        old_score = state.score
        state.score = score
        return old_score, state.score

    @staticmethod
    def stations(session, team_name):
        team = session.query(model.Team).filter_by(name=team_name).one_or_none()
        if not team:
            LOG.debug("Team %r not found!", team_name)
            return []
        if not team.route:
            return []
        return team.route.stations


class Station:
    @staticmethod
    def get(session, name):
        return session.query(model.Station).filter_by(name=name).one_or_none()

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
        route = (
            session.query(model.Route).filter_by(name=route_name).one_or_none()
        )
        return route.stations

    @staticmethod
    def assign_user(session, station_name, user_name):
        """
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        """
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        user = session.query(model.User).filter_by(name=user_name).one()
        station.users.add(user)
        return True

    @staticmethod
    def unassign_user(session, station_name, user_name):
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )

        found_user = None
        for user in station.users:
            if user.name == user_name:
                found_user = user
                break

        if found_user:
            station.users.remove(found_user)

        return True

    @staticmethod
    def team_states(
        session, station_name
    ) -> Generator[Tuple[str, TeamState, Optional[int], datetime], None, None]:
        # TODO this could be improved by just using one query
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        states = session.query(model.TeamStation).filter_by(
            station_name=station_name
        )
        mapping = {state.team_name: state for state in states}

        for route in station.routes:
            for team in route.teams:
                state = mapping.get(
                    team.name,
                    model.TeamStation(
                        team_name=team.name,
                        station_name=station_name,
                        state=TeamState.UNKNOWN,
                    ),
                )
                yield (team.name, state.state, state.score, state.updated)

    @staticmethod
    def accessible_by(session, username):
        user = session.query(model.User).filter_by(name=username).one_or_none()
        if not user:
            return set()
        return {station.name for station in user.stations}

    @staticmethod
    def related_team_states(
        session: scoped_session, station_name: str, relation: StationRelation
    ) -> Generator[Tuple[str, TeamState, Optional[int], datetime], None, None]:
        related_station = Station.related(session, station_name, relation)
        if not related_station:
            return
        yield from Station.team_states(session, related_station)

    @staticmethod
    def related(
        session: scoped_session, station_name: str, relation: StationRelation
    ) -> str:
        subquery = (
            session.query(model.Station.order)
            .filter_by(name=station_name)
            .scalar_subquery()
        )

        if relation == StationRelation.PREVIOUS:
            relation_filter = model.Station.order < subquery
        elif relation == StationRelation.NEXT:
            relation_filter = model.Station.order > subquery
        else:
            raise ValueError(f"Unsupported station-relation: {relation}")

        query = session.query(model.Station.name).filter(relation_filter)
        if relation == StationRelation.PREVIOUS:
            query = query.order_by(model.Station.order.desc())  # type: ignore
        elif relation == StationRelation.NEXT:
            query = query.order_by(model.Station.order)
        first_row = query.first()
        if first_row is None:
            return ""
        return first_row.name

    @staticmethod
    def assign_questionnaire(session, station_name, questionnaire_name):
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        questionnaire = (
            session.query(model.Questionnaire)
            .filter_by(name=questionnaire_name)
            .one()
        )
        if len(station.questionnaires) >= 1:
            raise PowonlineException(
                "Station already has a questionnaire assigned"
            )
        station.questionnaires.append(questionnaire)
        return True

    @staticmethod
    def unassign_questionnaire(session, station_name, questionnaire_name):
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        questionnaire = (
            session.query(model.Questionnaire)
            .filter_by(name=questionnaire_name)
            .one()
        )
        station.questionnaires.remove(questionnaire)
        return True


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
        team = session.query(model.Team).filter_by(name=team_name).one()
        if team.route:
            return False  # A team can only be assigned to one route
        route = session.query(model.Route).filter_by(name=route_name).one()
        route.teams.add(team)
        return True

    @staticmethod
    def unassign_team(session, route_name, team_name):
        route = session.query(model.Route).filter_by(name=route_name).one()
        team = session.query(model.Team).filter_by(name=team_name).one()
        route.teams.remove(team)
        return True

    @staticmethod
    def assign_station(session, route_name, station_name):
        route = session.query(model.Route).filter_by(name=route_name).one()
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        route.stations.add(station)
        return True

    @staticmethod
    def unassign_station(session, route_name, station_name):
        route = session.query(model.Route).filter_by(name=route_name).one()
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        route.stations.remove(station)
        return True

    @staticmethod
    def update_color(session, route_name, color_value):
        route = session.query(model.Route).filter_by(name=route_name).one()
        route.color = color_value
        return True


class User:
    @staticmethod
    def by_social_connection(
        session, provider, user_id, defaults=None
    ) -> model.User:
        defaults = defaults or {}
        query = session.query(model.OauthConnection).filter_by(
            provider_id=provider, provider_user_id=user_id
        )
        connection = query.one_or_none()
        if not connection:
            user = User.get(session, defaults["email"])
            if not user:
                random_pw = "".join(
                    SystemRandom().choice(ascii_letters + digits + punctuation)
                    for _ in range(64)
                )
                user = model.User(defaults["email"], password=random_pw)
            new_connection = model.OauthConnection()
            new_connection.user = user
            new_connection.provider_id = provider
            new_connection.provider_user_id = user_id
            new_connection.display_name = defaults.get("display_name")
            new_connection.image_url = defaults.get("avatar_url")
            session.add(new_connection)
            session.commit()
        else:
            user = connection.user
        return user

    @staticmethod
    def get(session, name) -> model.User | None:
        return session.query(model.User).filter_by(name=name).one_or_none()

    @staticmethod
    def delete(session, name):
        session.query(model.User).filter_by(name=name).delete()
        return None

    @staticmethod
    def create_new(session, data) -> model.User:
        user = model.User(**data)
        user = session.add(user)
        return user

    @staticmethod
    def all(session) -> Query[model.User]:
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
        if role and role in user.roles:
            user.roles.remove(role)
        return True

    @staticmethod
    def roles(session, user_name):
        user = session.query(model.User).filter_by(name=user_name).one()
        return user.roles

    @staticmethod
    def assign_station(session, user_name, station_name):
        """
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        """
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )
        user = session.query(model.User).filter_by(name=user_name).one()
        station.users.add(user)
        return True

    @staticmethod
    def unassign_station(session, user_name, station_name):
        station = (
            session.query(model.Station).filter_by(name=station_name).one()
        )

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
        user = session.query(model.User).filter_by(name=user_name).one_or_none()
        if not user:
            return False
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


class Upload:
    FALLBACK_FOLDER = "/tmp/uploads"

    @staticmethod
    def all(session):
        query = session.query(model.Upload)
        return query

    @staticmethod
    def list(session, username):
        query = session.query(model.Upload).filter_by(username=username)
        return query

    @staticmethod
    def make_thumbnail(session, uuid):
        query = session.query(model.Upload).filter_by(uuid=uuid)
        instance = query.one_or_none()
        if not instance:
            return

        thumbnail_folder = join(Upload.FALLBACK_FOLDER, "__thumbnails__")


class Questionnaire:
    @staticmethod
    def all(session):
        return session.query(model.Questionnaire).order_by(
            model.Questionnaire.order
        )

    @staticmethod
    def create_new(session, data):
        questionnaire = model.Questionnaire(**data)
        questionnaire = session.merge(questionnaire)
        return questionnaire

    @staticmethod
    def get(session, name):
        return (
            session.query(model.Questionnaire)
            .filter_by(name=name)
            .one_or_none()
        )

    @staticmethod
    def upsert(session, name, data):
        old = session.query(model.Questionnaire).filter_by(name=name).first()
        if not old:
            old = Questionnaire.create_new(session, data)
        for k, v in data.items():
            if k == "station_name" and not v:
                setattr(old, k, None)
            else:
                setattr(old, k, v)
        return old

    @staticmethod
    def delete(session, name):
        session.query(model.Questionnaire).filter_by(name=name).delete()
        return None

    @staticmethod
    def assigned_to_station(session, station_name):
        station = (
            session.query(model.Station)
            .filter_by(name=station_name)
            .one_or_none()
        )
        return station.questionnaires

    @staticmethod
    def assign_station(session, station_name, questionnaire_name):
        station = (
            session.query(model.Station)
            .filter_by(name=station_name)
            .one_or_none()
        )
        questionnaire = (
            session.query(model.Questionnaire)
            .filter_by(name=questionnaire_name)
            .one_or_none()
        )
        if not station or not questionnaire:
            return False
        if len(station.questionnaires) > 1:
            raise PowonlineException(
                "Station already has a questionnaire assigned"
            )
        if questionnaire.station and questionnaire.station != station:
            raise PowonlineException(
                "Questionnaire already assigned to another station"
            )
        station.questionnaires.add(questionnaire)
        return True

    @staticmethod
    def unassign_station(session, questionnaire_name):
        questionnaire = (
            session.query(model.Questionnaire)
            .filter_by(name=questionnaire_name)
            .one_or_none()
        )
        if not questionnaire:
            return False
        questionnaire.station = None
        return True
