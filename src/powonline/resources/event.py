import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import (
    EVENT_CO_ADMIN_ROLE,
    EVENT_OWNER_ROLE,
    User,
    get_user,
    require_event_admin_user,
)
from powonline.dependencies import get_db
from powonline.exc import NotFound

ROUTER = APIRouter(prefix="/events", tags=["event"])
LOG = logging.getLogger(__name__)

ALLOWED_MEMBER_ROLES = {EVENT_OWNER_ROLE, EVENT_CO_ADMIN_ROLE}


def _convert_time_range_for_db(data: dict[str, Any]) -> dict[str, Any]:
    """Convert TimeRange dict to SQLAlchemy Range object."""
    if "time_range" in data and isinstance(data["time_range"], dict):
        time_range_dict = data["time_range"]
        # Create a Range object with inclusive start, exclusive end
        data["time_range"] = Range(
            lower=time_range_dict["start"],
            upper=time_range_dict["end"]
        )
    return data


def _validate_member_role(role_name: str) -> None:
    if role_name not in ALLOWED_MEMBER_ROLES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown event role {role_name!r}. "
                f"Allowed values: {sorted(ALLOWED_MEMBER_ROLES)!r}"
            ),
        )


@ROUTER.get("")
async def list_events(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schema.ListResult[schema.EventSchema]:
    items = await core.Event.all(session)
    output = [schema.EventSchema.model_validate(item) for item in items]
    return schema.ListResult(items=output)


@ROUTER.post("", status_code=201)
async def create_event(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event: schema.EventCreateSchema = Body(),
) -> schema.EventSchema:
    data = _convert_time_range_for_db(event.model_dump())
    output = await core.Event.create_new(
        session,
        data=data,
        owner_name=auth_user.name,
    )
    return schema.EventSchema.model_validate(output)


@ROUTER.get("/{event_id}")
async def get_event(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
) -> schema.EventSchema:
    _ = auth_user
    output = await core.Event.get(session, event_id)
    if not output:
        raise NotFound("No such event")
    return schema.EventSchema.model_validate(output)


@ROUTER.put("/{event_id}")
async def update_event(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    event: schema.EventUpdateSchema = Body(),
) -> schema.EventSchema:
    _ = auth_user
    existing = await core.Event.get(session, event_id)
    if not existing:
        raise NotFound("No such event")

    data = _convert_time_range_for_db(event.model_dump(exclude_none=True))
    updated = await core.Event.update(
        session,
        existing,
        data,
    )
    return schema.EventSchema.model_validate(updated)


@ROUTER.get("/{event_id}/members")
async def list_event_members(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
) -> schema.ListResult[schema.EventMemberSchema]:
    _ = auth_user
    output = await core.Event.list_members(session, event_id)
    mapped = [schema.EventMemberSchema.model_validate(item) for item in output]
    return schema.ListResult(items=mapped)


@ROUTER.post("/{event_id}/members", status_code=201)
async def add_event_member(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    member: schema.EventMemberUpdateSchema = Body(),
) -> schema.EventMemberSchema:
    _ = auth_user
    _validate_member_role(member.role_name)

    event = await core.Event.get(session, event_id)
    if not event:
        raise NotFound("No such event")

    role = await core.Event.assign_member_role(
        session,
        event_id=event_id,
        user_name=member.user_name,
        role_name=member.role_name,
    )
    return schema.EventMemberSchema.model_validate(role)


@ROUTER.delete("/{event_id}/members/{user_name}/{role_name}")
async def remove_event_member(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    user_name: str,
    role_name: str,
):
    _ = auth_user
    _validate_member_role(role_name)

    await core.Event.revoke_member_role(
        session,
        event_id=event_id,
        user_name=user_name,
        role_name=role_name,
    )
    return Response(status_code=204)
