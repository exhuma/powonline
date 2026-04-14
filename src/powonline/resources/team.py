import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, require_event_admin_user
from powonline.dependencies import get_db, get_pusher
from powonline.exc import NotFound
from powonline.pusher import PusherWrapper

ROUTER = APIRouter(prefix="", tags=["team"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/events/{event_id}/team")
async def query_teams_for_event(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    quickfilter: str = "",
    assigned_to_route: str = "",
) -> schema.ListResult[schema.TeamSchema]:
    if quickfilter:
        func_name = "quickfilter_%s" % quickfilter
        filter_func = getattr(core.Team, func_name, None)
        if not filter_func:
            return Response(f"{quickfilter!r} is not a known quickfilter!", 400)
        quickfilter_teams = await filter_func(session)
        teams = [team for team in quickfilter_teams if team.event_id == event_id]
    elif assigned_to_route:
        teams = await core.Team.assigned_to_route(
            session, assigned_to_route, event_id=event_id
        )
    else:
        teams = await core.Team.all(session, event_id=event_id)

    output = [schema.TeamSchema.model_validate(item) for item in teams]
    return schema.ListResult(items=output)


@ROUTER.post("/events/{event_id}/team", status_code=201)
async def create_team_for_event(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    team: schema.TeamSchema = Body(),
) -> schema.TeamSchema:
    _ = auth_user
    payload = team.model_dump()
    payload["event_id"] = event_id
    output = await core.Team.create_new(session, payload)
    return schema.TeamSchema.model_validate(output)


@ROUTER.put("/events/{event_id}/team/{name}")
async def update_team_for_event(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
    team: schema.TeamSchema = Body(),
):
    _ = auth_user
    payload = team.model_dump()
    payload["event_id"] = event_id
    output = await core.Team.upsert(
        session,
        name,
        payload,
        event_id=event_id,
    )
    await session.flush()
    pusher.send_team_event("team-details-change", {"name": name})
    return schema.TeamSchema.model_validate(output)


@ROUTER.delete("/events/{event_id}/team/{name}")
async def delete_team_for_event(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
):
    _ = auth_user
    await core.Team.delete(session, name, event_id=event_id)
    pusher.send_team_event("team-deleted", {"name": name})
    return Response(None, 204)


@ROUTER.get("/events/{event_id}/team/{name}")
async def query_team_info_for_event(
    session: Annotated[AsyncSession, Depends(get_db)], event_id: int, name: str
):
    team = await core.Team.get(session, name, event_id=event_id)
    if not team:
        raise NotFound("No such team")
    return schema.TeamSchema.model_validate(team)


@ROUTER.get("/events/{event_id}/team/{team_name}/stations/{station_name}")
@ROUTER.get("/events/{event_id}/station/{station_name}/teams/{team_name}")
async def query_team_station_assignment(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    team_name: str,
    station_name: str,
):
    state = await core.Team.get_station_data(
        session,
        team_name,
        station_name,
        event_id=event_id,
    )
    if state.state:
        return schema.TeamStateInfo(state=state.state)
    else:
        return schema.TeamStateInfo(state=schema.TeamState.UNKNOWN)


@ROUTER.get("/events/{event_id}/team/{team_name}/stations")
async def get_stations_assigned_to_team(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    team_name: str,
):
    items = await core.Team.stations(session, team_name, event_id=event_id)
    ordered = sorted(items, key=lambda x: x.name)
    output = [schema.StationSchema.model_validate(item) for item in ordered]
    return output
