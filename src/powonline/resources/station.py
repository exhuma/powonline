import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import (
    User,
    get_user,
    require_event_admin_user,
    require_event_mutation_access,
)
from powonline.dependencies import get_db
from powonline.exc import AccessDenied, AuthDeniedReason

ROUTER = APIRouter(prefix="/events/{event_id}", tags=["station"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/station")
async def all_stations(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
) -> schema.ListResult[schema.StationSchema]:
    items = await core.Station.all(session, event_id=event_id)
    items = [schema.StationSchema.model_validate(item) for item in items]
    return schema.ListResult(items=items)


@ROUTER.post("/station", status_code=201)
async def create_new_station(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    station: schema.StationSchema = Body(),
) -> schema.StationSchema:
    auth_user.require_permission("admin_stations")
    payload = station.model_dump()
    payload["event_id"] = event_id
    output = await core.Station.create_new(session, payload)
    return schema.StationSchema.model_validate(output)


@ROUTER.get("/station/{name}")
@ROUTER.get("/station/{name}/related/{relation}")
async def query_stations(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
    relation: schema.StationRelation = schema.StationRelation.UNKNOWN,
) -> str:
    if relation == schema.StationRelation.UNKNOWN:
        station = await core.Station.get(session, name, event_id=event_id)
        return station.name if station else ""
    related_station = await core.Station.related(
        session,
        name,
        relation,
        event_id=event_id,
    )
    return related_station


@ROUTER.put("/station/{name}")
async def put(
    auth_user: Annotated[User, Depends(require_event_mutation_access)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
    station: schema.StationSchema = Body(),
):
    auth_user.require_permission("manage_station")
    has_access = await core.User.may_access_station(
        session, auth_user.name, name, event_id=event_id
    )
    if not ("admin" in auth_user.roles or has_access):
        raise AccessDenied(
            "Access denied to this station!",
            reason=AuthDeniedReason.ACCESS_DENIED,
        )
    payload = station.model_dump()
    payload["event_id"] = event_id
    output = await core.Station.upsert(
        session,
        name,
        payload,
        event_id=event_id,
    )
    return schema.StationSchema.model_validate(output)


@ROUTER.delete("/station/{name}")
async def delete_station(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
):
    auth_user.require_permission("admin_stations")
    await core.Station.delete(session, name, event_id=event_id)
    return Response(None, 204)


@ROUTER.get("/station/{station_name}/users/{user_name}")
@ROUTER.get("/user/{user_name}/stations/{station_name}")
async def is_user_assigned_to_station(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    user_name: str,
    station_name: str,
) -> bool:
    auth_user.require_permission("manage_permissions")
    station = await core.Station.get(session, station_name, event_id=event_id)
    if not station:
        return False
    user = await core.User.get(session, user_name)
    if not user:
        return False
    stations = {_.name for _ in user.stations or []}

    if station_name in stations:
        return True
    else:
        return False


@ROUTER.delete("/station/{station_name}/users/{user_name}")
@ROUTER.delete("/user/{user_name}/stations/{station_name}")
async def unassign_user_from_station(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    station_name,
    user_name,
):
    auth_user.require_permission("manage_permissions")
    station = await core.Station.get(session, station_name, event_id=event_id)
    if not station:
        return JSONResponse("Unknown station for event", 404)
    success = await core.Station.unassign_user(session, station_name, user_name)
    if success:
        return Response(None, 204)
    else:
        return JSONResponse("Unexpected error!", 500)


@ROUTER.post("/station/{station_name}/users")
async def assign_station_to_user(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    station_name: str,
    user: schema.UserSchema = Body(),
) -> Response:
    """
    Assigns a user to a station
    """
    auth_user.require_permission("manage_permissions")
    station = await core.Station.get(session, station_name, event_id=event_id)
    if not station:
        return JSONResponse("Unknown station for event", 404)
    success = await core.User.assign_station(session, user.name, station_name)
    if success:
        return JSONResponse("", 204)
    else:
        return JSONResponse("Station is already assigned to that user", 400)
