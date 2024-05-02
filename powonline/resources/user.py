import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User
from powonline.auth import get_user as get_auth_user
from powonline.db2api import map_user
from powonline.dependencies import get_db
from powonline.exc import NotFound

ROUTER = APIRouter(prefix="/user", tags=["user"])
LOG = logging.getLogger(__name__)


@ROUTER.get("")
async def query_users(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schema.ListResult[schema.UserSchema]:
    auth_user.require_permission("manage_permissions")
    users = await core.User.all(session)
    output = [await map_user(user) for user in users]
    return schema.ListResult(items=output)


@ROUTER.post("")
async def create_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user: schema.UserSchemaSensitive = Body(),
) -> schema.UserSchema:
    auth_user.require_permission("manage_permissions")
    output = await core.User.create_new(session, user.model_dump())
    return await map_user(output)


@ROUTER.get("/{name}")
async def get_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
) -> schema.UserSchema:
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, name)
    if not user:
        raise NotFound("No such user")
    return await map_user(user)


@ROUTER.put("/{name}")
async def update_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    user: schema.UserSchema = Body(),
):
    auth_user.require_permission("manage_permissions")
    output = await core.User.upsert(session, name, user)
    return schema.UserSchema.model_validate(output)


@ROUTER.delete("/{name}")
async def delete_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
):
    auth_user.require_permission("manage_permissions")
    await core.User.delete(session, name)
    return Response("", 204)


@ROUTER.get("/{user_name}/roles")
async def get_user_roles(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
) -> list[tuple[str, bool]]:
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, user_name)
    if not user:
        raise NotFound("No such user")
    all_roles = await core.Role.all(session)
    mapped_roles = await user.awaitable_attrs.roles
    user_roles = {role.name for role in mapped_roles or []}
    output = []
    for role in all_roles:
        output.append((role.name, role.name in user_roles))
    return output


@ROUTER.post("/{user_name}/roles")
async def assign_role_to_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
    role: schema.RoleSchema = Body(),
):
    """
    Assign a role to a user
    """
    auth_user.require_permission("manage_permissions")
    success = await core.User.assign_role(session, user_name, role.name)
    if success:
        return Response("", 204)
    return Response("Unexpected error!", 500)


@ROUTER.delete("/{user_name}/roles/{role_name}")
async def revoke_role_from_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name,
    role_name,
):
    auth_user.require_permission("manage_permissions")
    success = await core.User.unassign_role(session, user_name, role_name)
    if success:
        return Response("", 204)
    return Response("Unexpected error!", 500)


@ROUTER.get("/{user_name}/roles/{role_name}")
async def check_role_assignment_for_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
    role_name: str,
) -> bool:
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, user_name)
    if not user:
        raise NotFound("No such user")
    mapped_roles = await user.awaitable_attrs.roles
    roles = {_.name for _ in mapped_roles or []}
    if role_name in roles:
        return True
    return False


@ROUTER.get("/{user_name}/stations")
async def query_station_by_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str = Path(),
) -> list[tuple[str, bool]]:
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, user_name)
    if not user:
        raise NotFound("No such user")
    all_stations = await core.Station.all(session)
    user_stations = await user.awaitable_attrs.stations
    user_stations = {station.name for station in user_stations or []}
    output = []
    for station in all_stations:
        output.append((station.name, station.name in user_stations))
    return output


@ROUTER.post("/{user_name}/stations")
async def assign_user_to_station(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
    station: schema.StationSchema = Body(),
):
    """
    Assigns a user to a station
    """
    auth_user.require_permission("manage_permissions")
    success = await core.Station.assign_user(session, station.name, user_name)
    if success:
        return Response("", 204)
    else:
        return Response("Station is already assigned to that user", 400)
