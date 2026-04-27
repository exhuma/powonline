import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema, sse
from powonline.auth import User, get_optional_user, require_event_admin_user
from powonline.dependencies import get_db
from powonline.exc import NotFound
from powonline.schema import pii_responses

ROUTER = APIRouter(prefix="", tags=["team"])
LOG = logging.getLogger(__name__)

_CONTACT_PERMISSIONS = {"view_team_contact", "view_event_team_contact"}


def _can_view_contact(user: User | None) -> bool:
    """Return True when *user* holds any permission that grants PII access."""
    if user is None:
        return False
    return bool(user.permissions & _CONTACT_PERMISSIONS)


@ROUTER.get(
    "/events/{event_id}/team",
    response_model=None,
    responses=pii_responses(schema.TeamListFull, schema.TeamListPublic),
)
async def query_teams_for_event(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    user: Annotated[User | None, Depends(get_optional_user)],
    quickfilter: str = "",
    assigned_to_route: str = "",
) -> Response:
    if quickfilter:
        func_name = "quickfilter_%s" % quickfilter
        filter_func = getattr(core.Team, func_name, None)
        if not filter_func:
            return Response(f"{quickfilter!r} is not a known quickfilter!", 400)
        quickfilter_teams = await filter_func(session)
        teams = [
            team for team in quickfilter_teams if team.event_id == event_id
        ]
    elif assigned_to_route:
        teams = await core.Team.assigned_to_route(
            session, assigned_to_route, event_id=event_id
        )
    else:
        teams = await core.Team.all(session, event_id=event_id)

    if _can_view_contact(user):
        result = schema.TeamListFull(
            items=[schema.TeamSchema.model_validate(t) for t in teams]
        )
    else:
        result = schema.TeamListPublic(
            items=[schema.TeamSchemaPublic.model_validate(t) for t in teams]
        )
    return JSONResponse(content=result.model_dump(mode="json"))


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
    await sse.publish(
        event_id,
        "team-details-change",
        {
            "name": output.name,
            "route_name": output.route_name,
            "cancelled": output.cancelled,
            "accepted": output.accepted,
            "completed": output.completed,
            "order": output.order,
        },
    )
    return schema.TeamSchema.model_validate(output)


@ROUTER.delete("/events/{event_id}/team/{name}")
async def delete_team_for_event(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
):
    _ = auth_user
    await core.Team.delete(session, name, event_id=event_id)
    await sse.publish(event_id, "team-deleted", {"name": name})
    return Response(None, 204)


@ROUTER.get(
    "/events/{event_id}/team/{name}",
    response_model=None,
    responses=pii_responses(schema.TeamSchema, schema.TeamSchemaPublic),
)
async def query_team_info_for_event(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Response:
    team = await core.Team.get(session, name, event_id=event_id)
    if not team:
        raise NotFound("No such team")
    if _can_view_contact(user):
        result = schema.TeamSchema.model_validate(team)
    else:
        result = schema.TeamSchemaPublic.model_validate(team)
    return JSONResponse(content=result.model_dump(mode="json"))


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


@ROUTER.get(
    "/events/{event_id}/team/{team_name}/stations",
    response_model=None,
    responses=pii_responses(schema.StationListFull, schema.StationListPublic),
)
async def get_stations_assigned_to_team(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    team_name: str,
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Response:
    items = await core.Team.stations(session, team_name, event_id=event_id)
    ordered = sorted(items, key=lambda x: x.name)
    if _can_view_contact(user):
        result = schema.StationListFull(
            items=[schema.StationSchema.model_validate(s) for s in ordered]
        )
    else:
        result = schema.StationListPublic(
            items=[
                schema.StationSchemaPublic.model_validate(s) for s in ordered
            ]
        )
    return JSONResponse(content=result.model_dump(mode="json"))
