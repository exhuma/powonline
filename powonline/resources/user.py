import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User
from powonline.auth import get_user as get_auth_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/user", tags=["user"])
LOG = logging.getLogger(__name__)


@ROUTER.get("")
async def query_users(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    auth_user.require_permission("manage_permissions")
    users = await core.User.all(session)
    output = [schema.UserSchema.model_validate(user) for user in users]
    return output


@ROUTER.post("")
async def create_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user: schema.UserSchema = Body(),
):
    auth_user.require_permission("manage_permissions")
    output = await core.User.create_new(session, user.model_dump())
    return Response(schema.UserSchema.model_validate(output), 201)


@ROUTER.get("/{name}")
async def get_user(
    auth_user: Annotated[User, Depends(get_auth_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
):
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, name)
    if not user:
        return Response("No such user", 404)
    return schema.UserSchema.model_validate(user)


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
        return Response("No such user", 404)
    all_roles = await core.Role.all(session)
    user_roles = {role.name for role in user.roles or []}
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
        return Response("No such user", 404)
    roles = {_.name for _ in user.roles or []}
    if role_name in roles:
        return True
    return False
