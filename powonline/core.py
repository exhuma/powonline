import logging
import uuid
from configparser import ConfigParser
from datetime import datetime, timezone
from os import unlink
from os.path import join
from random import SystemRandom
from string import ascii_letters, digits, punctuation
from typing import Any, AsyncGenerator, Iterator, Optional, Tuple

from sqlalchemy import ScalarResult, and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import schema

from . import model
from .exc import (
    NoQuestionnaireForStation,
    NoSuchQuestionnaire,
    PowonlineException,
)
from .model import TeamState

LOG = logging.getLogger(__name__)


async def get_assignments(session: AsyncSession):
    routes = select(model.Route)

    output = {
        "teams": {},
        "stations": {},
    }

    result = await session.execute(routes)
    for route in result.scalars():
        output["teams"][route.name] = await route.awaitable_attrs.teams
        output["stations"][route.name] = await route.awaitable_attrs.stations

    return output


def make_default_team_state():
    return {"state": TeamState.UNKNOWN}


async def scoreboard(session: AsyncSession) -> Iterator[tuple[str, int]]:
    query = select(model.Team)
    teams = await session.execute(query)
    scores: dict[str, int] = {}
    for row in teams.scalars():
        station_score = sum(
            state.score for state in await row.awaitable_attrs.station_states
        )
        quest_score = sum(
            quest.score
            for quest in await row.awaitable_attrs.questionnaire_scores
        )
        scores[row.name] = sum([station_score, quest_score])
    output = reversed(sorted(scores.items(), key=lambda x: x[1]))
    return output


async def questionnaire_scores(
    session: AsyncSession,
) -> dict[str, dict[str, dict[str, str | int]]]:
    output: dict[str, dict[str, dict[str, str | int]]] = {}
    query = select(model.TeamQuestionnaire).join(model.Questionnaire)
    result = await session.execute(query)
    for row in result.scalars():
        questionnaire_name: str = row.questionnaire_name  # type: ignore
        score: int = row.score  # type: ignore
        station = (
            row.questionnaire.station.name
            if row.questionnaire and row.questionnaire.station
            else ""
        )
        team_stations = output.setdefault(row.team_name, {})

        team_stations[station] = {
            "name": questionnaire_name,
            "score": score,
        }
    return output


def add_audit_log(
    session: AsyncSession, username: str, type_: model.AuditType, message: str
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


async def set_questionnaire_score(
    session: AsyncSession, team: str, station: str, score: int
):
    """
    Set the team-score for a questionaire on a given station.
    """
    station_query = select(model.Station).filter_by(name=station)
    station_entity = session.execute(station_query).scalar_one_or_none()
    if not station_entity:
        raise PowonlineException(f"Station {station} not found")

    questionnaires = await station_entity.awaitable_attrs.questionnaires
    if not questionnaires:
        raise NoQuestionnaireForStation(station_entity)

    if len(questionnaires) > 1:
        raise NoQuestionnaireForStation(
            station_entity, "Multiple questionnaires assigned"
        )

    existing_questionnaire = questionnaires[0]
    questionnaire_name = existing_questionnaire.name

    query = select(model.TeamQuestionnaire).filter_by(
        team_name=team, questionnaire_name=questionnaire_name
    )
    result = await session.execute(query)
    state = result.scalar_one_or_none()
    if not state:
        state = model.TeamQuestionnaire(team, questionnaire_name, score)
        session.add(state)
    old_score = state.score
    state.score = score
    return old_score, score


async def global_dashboard(session: AsyncSession):
    teams_query = select(model.Team).order_by(model.Team.name)
    stations_query = select(model.Station).order_by(model.Station.name)
    teams = await session.execute(teams_query)
    stations = await session.execute(stations_query)
    team_names = set()
    station_names = set()
    output: list[schema.GlobalDashboardRow] = []
    for team in teams.scalars():
        team_names.add(team.name)
        team_data = schema.GlobalDashboardRow(stations=[], team=team.name)
        team_route = await team.awaitable_attrs.route
        if team_route:
            reachable_stations = {
                station.name
                for station in await team_route.awaitable_attrs.stations
            }
        else:
            reachable_stations = set()
        for station in stations.scalars():
            station_names.add(station.name)
            if station.name in reachable_stations:
                team_states_query = select(model.TeamStation).filter(
                    and_(
                        model.TeamStation.team == team,
                        model.TeamStation.station == station,
                    )
                )
                result = await session.execute(team_states_query)
                dbstate = result.scalar_one_or_none()
                if dbstate:
                    cell_state = dbstate.state
                    cell_score = dbstate.score
                else:
                    cell_state = TeamState.UNKNOWN
                    cell_score = 0
            else:
                cell_state = TeamState.UNREACHABLE
                cell_score = 0
            team_data.stations.append(
                schema.GlobalDashboardStation(
                    name=station.name,
                    score=cell_score or 0,
                    state=cell_state or TeamState.UNKNOWN,
                )
            )
        output.append(team_data)
    return output


class Team:
    @staticmethod
    async def all(session: AsyncSession) -> ScalarResult[model.Team]:
        query = select(model.Team).order_by(model.Team.effective_start_time)
        result = await session.execute(query)
        return result.scalars()

    @staticmethod
    async def get(session: AsyncSession, name: str) -> model.Team | None:
        query = select(model.Team).filter_by(name=name)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def quickfilter_without_route(
        session: AsyncSession,
    ) -> ScalarResult[model.Team]:
        query = select(model.Team).filter(
            model.Team.route == None  # noqa: E711
        )
        result = await session.execute(query)
        return result.scalars()

    @staticmethod
    async def assigned_to_route(
        session: AsyncSession, route_name: str
    ) -> list[model.Team]:
        query = select(model.Route).filter_by(name=route_name)
        result = await session.execute(query)
        route = result.scalar_one()
        return await route.awaitable_attrs.teams

    @staticmethod
    async def create_new(
        session: AsyncSession, data: dict[str, Any]
    ) -> model.Team:
        team = model.Team(**data)
        if not data.get("confirmation_key"):
            team.reset_confirmation_key()
        team = await session.merge(team)
        return team

    @staticmethod
    async def upsert(
        session: AsyncSession, name: str, data: dict[str, Any]
    ) -> model.Team:
        data.pop("inserted", None)
        data.pop("updated", None)
        old_query = select(model.Team).filter_by(name=name)
        old_result = await session.execute(old_query)
        old = old_result.scalar_one_or_none()
        if not old:
            old = await Team.create_new(session, data)
        for k, v in data.items():
            setattr(old, k, v)
        return old

    @staticmethod
    async def delete(session: AsyncSession, name: str) -> None:
        query = delete(model.Team).filter_by(name=name)
        await session.execute(query)
        return None

    @staticmethod
    async def get_station_data(
        session: AsyncSession, team_name: str, station_name: str
    ) -> model.TeamStation:
        query = select(model.TeamStation).filter_by(
            team_name=team_name, station_name=station_name
        )
        result = await session.execute(query)
        state = result.scalar_one_or_none()
        if not state:
            return model.TeamStation(
                team_name=team_name, station_name=station_name
            )
        else:
            return state

    @staticmethod
    async def advance_on_station(
        session: AsyncSession, team_name: str, station_name: str
    ) -> TeamState:
        query = select(model.TeamStation).filter_by(
            team_name=team_name, station_name=station_name
        )
        result = await session.execute(query)
        state = result.scalar_one_or_none()
        if not state:
            state = model.TeamStation(
                team_name=team_name, station_name=station_name
            )
            state = await session.merge(state)
            await session.flush()

        state_team = await state.awaitable_attrs.team
        state_station = await state.awaitable_attrs.station
        if state.state == TeamState.UNKNOWN:
            state.state = TeamState.ARRIVED
            # Teams which arrive at the finish station will have their
            # finish-time set
            if not state_team.finish_time and state_station.is_end:
                state_team.finish_time = func.now()
        elif state.state == TeamState.ARRIVED:
            # Teams which leave the departure station will have their
            # start-time set
            if not state_team.effective_start_time and state_station.is_start:
                state_team.effective_start_time = func.now()
            state.state = TeamState.FINISHED
        else:
            state.state = TeamState.UNKNOWN
        return state.state

    @staticmethod
    async def set_station_score(
        session: AsyncSession, team_name: str, station_name: str, score: int
    ) -> tuple[int | None, int]:
        query = select(model.TeamStation).filter_by(
            team_name=team_name, station_name=station_name
        )
        result = await session.execute(query)
        state = result.scalar_one_or_none()

        if not state:
            state = model.TeamStation(
                team_name=team_name, station_name=station_name
            )
            state = await session.merge(state)
        old_score = state.score
        state.score = score
        return old_score, state.score

    @staticmethod
    async def stations(
        session: AsyncSession, team_name: str
    ) -> list[model.Station]:
        query = select(model.Team).filter_by(name=team_name)
        result = await session.execute(query)
        team = result.scalar_one_or_none()
        if not team:
            LOG.debug("Team %r not found!", team_name)
            return []
        if not team.route:
            return []
        route = await team.awaitable_attrs.route
        stations = await route.awaitable_attrs.stations
        return stations


class Station:
    @staticmethod
    def get(session, name):
        return session.query(model.Station).filter_by(name=name).one_or_none()

    @staticmethod
    async def all(session: AsyncSession) -> ScalarResult[model.Station]:
        query = select(model.Station).order_by(model.Station.order)
        return (await session.execute(query)).scalars()

    @staticmethod
    async def create_new(
        session: AsyncSession, data: dict[str, Any]
    ) -> model.Station:
        station = model.Station(**data)
        station = await session.merge(station)
        return station

    @staticmethod
    async def upsert(
        session: AsyncSession, name: str, data: dict[str, Any]
    ) -> model.Station:
        query = select(model.Station).filter_by(name=name)
        result = await session.execute(query)
        old = result.scalar_one()
        if not old:
            old = await Station.create_new(session, data)
        for k, v in data.items():
            setattr(old, k, v)
        return old

    @staticmethod
    async def delete(session: AsyncSession, name: str) -> None:
        query = delete(model.Station).filter_by(name=name)
        await session.execute(query)
        return None

    @staticmethod
    async def assigned_to_route(
        session: AsyncSession, route_name: str
    ) -> list[model.Station]:
        query = select(model.Route).filter_by(name=route_name)
        result = await session.execute(query)
        route = result.scalar_one()
        return await route.awaitable_attrs.stations

    @staticmethod
    async def assign_user(
        session: AsyncSession, station_name: str, user_name: str
    ) -> bool:
        """
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        """
        station_query = select(model.Station).filter_by(name=station_name)
        station_result = await session.execute(station_query)
        station = station_result.scalar_one()
        user_query = select(model.User).filter_by(name=user_name)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one()
        station_users = await station.awaitable_attrs.users
        station_users.add(user)
        return True

    @staticmethod
    async def unassign_user(
        session: AsyncSession, station_name: str, user_name: str
    ) -> bool:
        station_query = select(model.Station).filter_by(name=station_name)
        station_result = await session.execute(station_query)
        station = station_result.scalar_one()
        found_user = None
        station_users = await station.awaitable_attrs.users
        for user in await station_users:
            if user.name == user_name:
                found_user = user
                break

        if found_user:
            station_users.remove(found_user)

        return True

    @staticmethod
    async def team_states(
        session: AsyncSession, station_name: str
    ) -> AsyncGenerator[Tuple[str, TeamState, Optional[int], datetime], None]:
        # TODO this could be improved by just using one query
        station_query = select(model.Station).filter_by(name=station_name)
        station = (await session.execute(station_query)).scalars().one()
        states_query = select(model.TeamStation).filter_by(
            station_name=station_name
        )
        states = await session.execute(states_query)
        mapping = {state.team_name: state for state in states.scalars()}

        for route in await station.awaitable_attrs.routes:
            for team in await route.awaitable_attrs.teams:
                state = mapping.get(
                    team.name,
                    model.TeamStation(
                        team_name=team.name,
                        station_name=station_name,
                        state=TeamState.UNKNOWN,
                    ),
                )
                yield (
                    team.name,
                    state.state or TeamState.UNKNOWN,
                    state.score,
                    state.updated,
                )

    @staticmethod
    async def accessible_by(session: AsyncSession, username: str) -> set[str]:
        query = select(model.User).filter_by(name=username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return set()
        return {station.name for station in await user.awaitable_attrs.stations}

    @staticmethod
    async def related_team_states(
        session: AsyncSession,
        station_name: str,
        relation: schema.StationRelation,
    ) -> AsyncGenerator[Tuple[str, TeamState, Optional[int], datetime], None]:
        related_station = await Station.related(session, station_name, relation)
        if not related_station:
            return
        async for state in Station.team_states(session, related_station):
            yield state

    @staticmethod
    async def related(
        session: AsyncSession,
        station_name: str,
        relation: schema.StationRelation,
    ) -> str:
        subquery = (
            select(model.Station.order)
            .filter_by(name=station_name)
            .scalar_subquery()
        )
        if relation == schema.StationRelation.PREVIOUS:
            relation_filter = model.Station.order < subquery
        elif relation == schema.StationRelation.NEXT:
            relation_filter = model.Station.order > subquery
        else:
            raise ValueError(f"Unsupported station-relation: {relation}")

        query = select(model.Station.name).filter(relation_filter)
        if relation == schema.StationRelation.PREVIOUS:
            query = query.order_by(model.Station.order.desc())
        elif relation == schema.StationRelation.NEXT:
            query = query.order_by(model.Station.order)

        result = await session.execute(query)
        first_row = result.first()
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
    async def all(session: AsyncSession) -> ScalarResult[model.Route]:
        return (await session.execute(select(model.Route))).scalars()

    @staticmethod
    async def create_new(
        session: AsyncSession, data: dict[str, Any]
    ) -> model.Route:
        route = model.Route(**data)
        route = await session.merge(route)
        return route

    @staticmethod
    async def upsert(
        session: AsyncSession, name: str, data: dict[str, Any]
    ) -> model.Route:
        old_query = select(model.Route).filter_by(name=name)
        old_result = await session.execute(old_query)
        old = old_result.scalar_one_or_none()
        if not old:
            old = await Route.create_new(session, data)
        for k, v in data.items():
            setattr(old, k, v)
        return old

    @staticmethod
    async def delete(session: AsyncSession, name: str) -> None:
        delete_query = delete(model.Route).filter_by(name=name)
        await session.execute(delete_query)
        return None

    @staticmethod
    async def assign_team(
        session: AsyncSession, route_name: str, team_name: str
    ) -> bool:
        team_query = select(model.Team).filter_by(name=team_name)
        team = (await session.execute(team_query)).scalar_one()
        team_route = await team.awaitable_attrs.route
        if team_route:
            return False  # A team can only be assigned to one route
        route_query = select(model.Route).filter_by(name=route_name)
        route = (await session.execute(route_query)).scalar_one()
        route_teams = await route.awaitable_attrs.teams
        route_teams.add(team)
        return True

    @staticmethod
    async def unassign_team(
        session: AsyncSession, route_name: str, team_name: str
    ) -> bool:
        route_query = select(model.Route).filter_by(name=route_name)
        route = (await session.execute(route_query)).scalar_one()
        team_query = select(model.Team).filter_by(name=team_name)
        team = (await session.execute(team_query)).scalar_one()
        route_teams = await route.awaitable_attrs.teams
        route_teams.remove(team)
        return True

    @staticmethod
    async def assign_station(
        session: AsyncSession, route_name: str, station_name: str
    ) -> bool:
        route_query = select(model.Route).filter_by(name=route_name)
        route = (await session.execute(route_query)).scalar_one()
        station_query = select(model.Station).filter_by(name=station_name)
        station = (await session.execute(station_query)).scalar_one()
        route_stations = await route.awaitable_attrs.stations
        route_stations.add(station)
        return True

    @staticmethod
    async def unassign_station(
        session: AsyncSession, route_name: str, station_name: str
    ) -> bool:
        route_query = select(model.Route).filter_by(name=route_name)
        route = (await session.execute(route_query)).scalar_one()
        station_query = select(model.Station).filter_by(name=station_name)
        station = (await session.execute(station_query)).scalar_one()
        route_stations = await route.awaitable_attrs.stations
        route_stations.remove(station)
        return True

    @staticmethod
    async def update_color(
        session: AsyncSession, route_name: str, color_value: str
    ) -> bool:
        route_query = select(model.Route).filter_by(name=route_name)
        route = (await session.execute(route_query)).scalar_one()
        route.color = color_value
        return True


class User:
    @staticmethod
    async def by_social_connection(
        session: AsyncSession,
        provider: str,
        user_id: str,
        defaults: dict[str, Any] | None = None,
    ) -> model.User:
        defaults = defaults or {}
        oauth_query = select(model.OauthConnection).filter_by(
            provider_id=provider, provider_user_id=user_id
        )
        oauth_result = await session.execute(oauth_query)
        connection = oauth_result.scalar_one_or_none()
        if not connection:
            user = await User.get(session, defaults["email"])
            if not user:
                random_pw = "".join(
                    SystemRandom().choice(ascii_letters + digits + punctuation)
                    for _ in range(64)
                )
                user = model.User(name=defaults["email"], password=random_pw)
            new_connection = model.OauthConnection()
            new_connection.user = user
            new_connection.provider_id = provider
            new_connection.provider_user_id = user_id
            new_connection.display_name = defaults.get("display_name")
            new_connection.image_url = defaults.get("avatar_url")
            session.add(new_connection)
            await session.commit()
        else:
            user = await connection.awaitable_attrs.user
        return user

    @staticmethod
    async def get(session: AsyncSession, name: str) -> model.User | None:
        query = select(model.User).filter_by(name=name)
        user = (await session.execute(query)).scalar_one_or_none()
        return user

    @staticmethod
    async def delete(session: AsyncSession, name: str) -> None:
        query = delete(model.User).filter_by(name=name)
        await session.execute(query)
        return None

    @staticmethod
    async def create_new(
        session: AsyncSession, data: dict[str, Any]
    ) -> model.User:
        data.pop("avatar_url", None)  # Avatars are not settable
        user = model.User(**data)
        session.add(user)
        return user

    @staticmethod
    async def all(session: AsyncSession) -> ScalarResult[model.User]:
        query = select(model.User)
        result = await session.execute(query)
        return result.scalars()

    @staticmethod
    async def assign_role(
        session: AsyncSession, user_name: str, role_name: str
    ) -> bool:
        user_query = select(model.User).filter_by(name=user_name)
        user = (await session.execute(user_query)).scalar_one()
        role_query = select(model.Role).filter_by(name=role_name)
        role = (await session.execute(role_query)).scalar_one()
        user_roles = await user.awaitable_attrs.roles
        user_roles.add(role)
        return True

    @staticmethod
    async def unassign_role(
        session: AsyncSession, user_name: str, role_name: str
    ) -> bool:
        user_query = select(model.User).filter_by(name=user_name)
        user = (await session.execute(user_query)).scalar_one()
        role_query = select(model.Role).filter_by(name=role_name)
        role = (await session.execute(role_query)).scalar_one_or_none()
        user_roles = await user.awaitable_attrs.roles
        if role and role in user_roles:
            user.roles.remove(role)
        return True

    @staticmethod
    async def roles(session: AsyncSession, user_name: str) -> set[model.Role]:
        user_query = select(model.User).filter_by(name=user_name)
        user = (await session.execute(user_query)).scalar_one()
        roles = await user.awaitable_attrs.roles
        return roles

    @staticmethod
    async def assign_station(
        session: AsyncSession, user_name: str, station_name: str
    ) -> bool:
        """
        Returns true if the operation worked, false if the use is already
        assigned to another station.
        """
        station_query = select(model.Station).filter_by(name=station_name)
        station = (await session.execute(station_query)).scalar_one()
        user_query = select(model.User).filter_by(name=user_name)
        user = (await session.execute(user_query)).scalar_one()
        station_users = await station.awaitable_attrs.users
        station_users.add(user)
        return True

    @staticmethod
    async def unassign_station(
        session: AsyncSession, user_name: str, station_name: str
    ) -> bool:
        station_query = select(model.Station).filter_by(name=station_name)
        station = (await session.execute(station_query)).scalar_one()
        station_users = await station.awaitable_attrs.users

        found_user = None
        for user in station_users:
            if user.name == user_name:
                found_user = user
                break

        if found_user:
            station_users.remove(found_user)

        return True

    @staticmethod
    async def may_access_station(
        session: AsyncSession, user_name: str, station_name: str
    ) -> bool:
        user_query = select(model.User).filter_by(name=user_name)
        user = (await session.execute(user_query)).scalar_one()
        if not user:
            return False
        user_stations = {_.name for _ in await user.awaitable_attrs.stations}
        return station_name in user_stations


class Role:
    @staticmethod
    async def get(session: AsyncSession, name: str) -> model.Role | None:
        query = select(model.Role).filter_by(name=name)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, name: str) -> None:
        query = delete(model.Role).filter_by(name=name)
        await session.execute(query)
        return None

    @staticmethod
    async def create_new(
        session: AsyncSession, data: dict[str, Any]
    ) -> model.Role:
        role = model.Role(**data)
        session.add(role)
        return role

    @staticmethod
    async def all(session: AsyncSession) -> ScalarResult[model.Role]:
        query = select(model.Role)
        result = await session.execute(query)
        return result.scalars()


class Upload:
    FALLBACK_FOLDER = "/tmp/uploads"

    @staticmethod
    async def all(session: AsyncSession) -> ScalarResult[model.Upload]:
        query = select(model.Upload)
        result = await session.execute(query)
        return result.scalars()

    @staticmethod
    async def list(
        session: AsyncSession, username: str
    ) -> ScalarResult[model.Upload]:
        query = select(model.Upload).filter_by(username=username)
        result = await session.execute(query)
        return result.scalars()

    @staticmethod
    async def make_thumbnail(
        session: AsyncSession, uuid: str
    ) -> model.Upload | None:
        query = select(model.Upload).filter_by(uuid=uuid)
        result = await session.execute(query)
        instance = result.scalar_one_or_none()
        if not instance:
            return
        thumbnail_folder = join(Upload.FALLBACK_FOLDER, "__thumbnails__")

    @staticmethod
    async def store(
        session: AsyncSession, user_name: str, relative_target: str
    ) -> model.Upload:
        query = select(model.Upload).filter_by(
            filename=relative_target, username=user_name
        )
        result = await session.execute(query)
        db_instance = result.scalar_one_or_none()
        if not db_instance:
            db_instance = model.Upload(relative_target, user_name)
            session.add(db_instance)
            await session.flush()
        return db_instance

    @staticmethod
    async def by_id(
        session: AsyncSession, uuid: uuid.UUID
    ) -> model.Upload | None:
        """
        Returns an upload entity by its UUID
        """
        query = select(model.Upload).filter_by(uuid=uuid)
        result = await session.execute(query)
        instance = result.scalar_one_or_none()
        return instance

    @staticmethod
    async def delete(
        session: AsyncSession, data_folder: str, instance: model.Upload
    ):
        fullname = join(data_folder, instance.filename)
        unlink(fullname)
        await session.delete(instance)
        await session.commit()


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
