import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User
from powonline.auth import get_user as get_auth_user
from powonline.db2api import map_user
from powonline.dependencies import get_db
from powonline.exc import NotFound
from powonline.routers.auth import _clear_auth_cookies

ROUTER = APIRouter(prefix="/user", tags=["user"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/me/admin-events")
async def list_my_admin_events(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schema.ListResult[schema.EventSchema]:
    """
    Return upcoming events where the authenticated user is event_owner or
    event_co_admin.  Used by the user-management UI to populate the event
    dropdown when assigning stations to a user.
    """
    items = await core.Event.all_admin_upcoming(session, auth_user)
    output = [schema.EventSchema.model_validate(item) for item in items]
    return schema.ListResult(items=output)


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


@ROUTER.delete("/me")
async def delete_my_account(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    GDPR right to erasure — self-service account deletion.

    The authenticated user's account and all associated personal data are
    permanently removed:
    - OAuth connections
    - File uploads
    - Role assignments (global and per-event)
    - Station assignments
    - Messages authored by this user

    Teams *owned* by the user are **reassigned** to a system sentinel
    (``__deleted__``) rather than deleted, so that event history (scores,
    progress states) is preserved for other participants.

    Audit log entries are retained but the ``username`` field is nulled to
    comply with data minimisation requirements while preserving operational
    integrity.

    On success the access and refresh cookies are cleared, effectively
    terminating the session.
    """
    await core.User.delete_self(session, auth_user.username)
    response = Response("", 204)
    _clear_auth_cookies(response)
    return response


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
    event_id: int | None = Query(default=None),
) -> list[tuple[str, bool]]:
    """
    Return all stations (optionally scoped to an event) with a boolean
    indicating whether each station is assigned to the given user.

    This endpoint is freely accessible to any authenticated user so that the
    frontend can determine which station dashboards a user may open.
    """
    user = await core.User.get(session, user_name)
    if not user:
        raise NotFound("No such user")
    all_stations = await core.Station.all(session, event_id=event_id)
    user_stations = await user.awaitable_attrs.stations
    user_station_names = {station.name for station in user_stations or []}
    output = []
    for station in all_stations:
        output.append((station.name, station.name in user_station_names))
    return output


@ROUTER.post("/{user_name}/stations")
async def assign_user_to_station(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
    station: schema.StationSchema = Body(),
    event_id: int | None = Query(default=None),
):
    """
    Assigns a user to a station (optionally scoped to an event).
    """
    auth_user.require_permission("manage_permissions")
    success = await core.Station.assign_user(
        session, station.name, user_name, event_id=event_id
    )
    if success:
        return Response("", 204)
    else:
        return Response("Station is already assigned to that user", 400)


@ROUTER.delete("/{user_name}/stations/{station_name}")
async def unassign_user_from_station(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
    station_name: str = Path(),
    event_id: int | None = Query(default=None),
):
    """
    Removes a station assignment from a user (optionally scoped to an event).
    """
    auth_user.require_permission("manage_permissions")
    await core.Station.unassign_user(
        session, station_name, user_name, event_id=event_id
    )
    return Response("", 204)
