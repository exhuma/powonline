import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, get_user
from powonline.dependencies import get_db, get_pusher
from powonline.exc import NotFound
from powonline.pusher import PusherWrapper

ROUTER = APIRouter(prefix="", tags=["team"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/team")
async def query_teams(
    session: Annotated[AsyncSession, Depends(get_db)],
    quickfilter: str = "",
    assigned_to_route: str = "",
) -> schema.ListResult[schema.TeamSchema]:
    if quickfilter:
        func_name = "quickfilter_%s" % quickfilter
        filter_func = getattr(core.Team, func_name, None)
        if not filter_func:
            return Response(f"{quickfilter!r} is not a known quickfilter!", 400)
        teams = filter_func(session)
    elif assigned_to_route:
        teams = await core.Team.assigned_to_route(session, assigned_to_route)
    else:
        teams = await core.Team.all(session)

    output = [schema.TeamSchema.model_validate(item) for item in teams]
    return schema.ListResult(items=output)


@ROUTER.post("/team", status_code=201)
async def create_team(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    team: schema.TeamSchema = Body(),
) -> schema.TeamSchema:
    auth_user.require_permission("admin_teams")
    output = await core.Team.create_new(session, team.model_dump())
    return schema.TeamSchema.model_validate(output)


@ROUTER.put("/team/{name}")
async def update_team(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
    team: schema.TeamSchema = Body(),
):
    auth_user.require_permission("admin_teams")
    output = await core.Team.upsert(session, name, team.model_dump())
    await session.flush()
    pusher.send_team_event("team-details-change", {"name": name})
    return schema.TeamSchema.model_validate(output)


@ROUTER.delete("/team/{name}")
async def delete_team(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
):
    auth_user.require_permission("admin_teams")
    await core.Team.delete(session, name)
    pusher.send_team_event("team-deleted", {"name": name})
    return Response(None, 204)


@ROUTER.get("/team/{name}")
async def query_team_info(
    session: Annotated[AsyncSession, Depends(get_db)], name: str
):
    team = await core.Team.get(session, name)
    if not team:
        raise NotFound("No such team")
    return schema.TeamSchema.model_validate(team)


@ROUTER.get("/team/{team_name}/stations/{station_name}")
@ROUTER.get("/station/{station_name}/teams/{team_name}")
async def query_team_station_assignment(
    session: Annotated[AsyncSession, Depends(get_db)],
    team_name: str,
    station_name: str,
):
    state = await core.Team.get_station_data(session, team_name, station_name)
    if state.state:
        return schema.TeamStateInfo(state=state.state)
    else:
        return schema.TeamStateInfo(state=schema.TeamState.UNKNOWN)


@ROUTER.get("/team/{team_name}/stations")
async def get_stations_assigned_to_team(
    session: Annotated[AsyncSession, Depends(get_db)], team_name: str
):
    items = await core.Team.stations(session, team_name)
    ordered = sorted(items, key=lambda x: x.name)
    output = [schema.StationSchema.model_validate(item) for item in ordered]
    return output
