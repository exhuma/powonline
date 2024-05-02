import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, get_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/station", tags=["station"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/station")
async def all_stations(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[schema.StationSchema]:
    items = await core.Station.all(session)
    items = [schema.StationSchema.model_validate(item) for item in items]
    return items


@ROUTER.post("/station")
async def create_new_station(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    station: schema.StationSchema = Body(),
):
    auth_user.require_permission("admin_stations")
    output = await core.Station.create_new(session, station.model_dump())
    return Response(schema.StationSchema.model_validate(output), 201)


@ROUTER.get("/station/{name}")
@ROUTER.get("/station/{name}/related/{relation}")
async def query_stations(
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    relation: schema.StationRelation = schema.StationRelation.UNKNOWN,
) -> str:
    related_station = await core.Station.related(session, name, relation)
    return related_station


@ROUTER.put("/station/{name}")
def put(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    station: schema.StationSchema = Body(),
):
    auth_user.require_permission("manage_station")
    if "admin" not in auth_user.roles and not core.User.may_access_station(
        session, auth_user.name, name
    ):
        return "Access denied to this station!", 401

    output = core.Station.upsert(session, name, station.model_dump())
    return schema.StationSchema.model_validate(output)


@ROUTER.delete("/station/{name}")
async def delete_station(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
):
    auth_user.require_permission("admin_stations")
    await core.Station.delete(session, name)
    return Response(None, 204)


@ROUTER.get("/station/{station_name}/users/{user_name}")
@ROUTER.get("/user/{user_name}/stations/{station_name}")
async def is_user_assigned_to_station(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
    station_name: str,
) -> bool:
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, user_name)
    if not user:
        return False
    stations = {_.name for _ in user.stations or []}

    if station_name in stations:
        return True
    else:
        return False


@ROUTER.get("/station/{station_name}/users/{user_name}")
@ROUTER.get("/user/{user_name}/stations/{station_name}")
async def unassign_user_from_station(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    station_name,
    user_name,
):
    auth_user.require_permission("manage_permissions")
    success = await core.Station.unassign_user(session, station_name, user_name)
    if success:
        return "", 204
    else:
        return "Unexpected error!", 500
