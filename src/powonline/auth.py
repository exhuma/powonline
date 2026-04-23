import logging
from configparser import ConfigParser
from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Path
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from powonline.config import default
from powonline.dependencies import get_db
from powonline.exc import AccessDenied, AuthDeniedReason
from powonline.model import Event, EventUserRole

LOG = logging.getLogger(__name__)
AUTH_LOG = logging.getLogger("auth")

PERMISSION_MAP = {
    "admin": {
        "admin_files",
        "admin_routes",
        "admin_stations",
        "admin_teams",
        "admin_events",
        "manage_permissions",
        "manage_station",
        "view_audit_log",
        "view_team_contact",
    },
    "staff": {
        "view_team_contact",
    },
    "station_manager": {
        "manage_station",
    },
    "event_owner": {
        "manage_event",
        "manage_event_members",
        "bypass_event_window",
    },
    "event_co_admin": {
        "manage_event",
        "manage_event_members",
        "bypass_event_window",
    },
}

EVENT_OWNER_ROLE = "event_owner"
EVENT_CO_ADMIN_ROLE = "event_co_admin"

LOCAL_AUTH = HTTPBasic(
    auto_error=False, description="Authentication for local-development"
)
Bearer = HTTPBearer(auto_error=False)


class User(BaseModel):
    name: str
    roles: set[str]

    @property
    def permissions(self) -> set[str]:
        all_permissions = set()
        for role in self.roles:
            all_permissions |= PERMISSION_MAP.get(role, set())
        return all_permissions

    def require_any_permission(self, permissions: set[str]) -> None:
        # by removing the users permissions from the required permissions,
        # we will end up with an empty set if the user is granted access.
        # All remaining permissions are those that the user was not granted
        # (the user is missing those permissions to gain entry).
        # Hence, if the resulting set is non-empty, we block access.
        missing_permissions = permissions - self.permissions
        if missing_permissions:
            LOG.debug(
                "User was missing the following permissions: %r",
                missing_permissions,
            )
            raise AccessDenied("Access Denied (Not enough permissions)!")

    def require_permission(self, permission: str) -> None:
        self.require_any_permission({permission})

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


def local_dev_user(
    basic_credentials: Annotated[
        HTTPBasicCredentials | None, Depends(LOCAL_AUTH)
    ],
) -> User | None:
    """
    Implementation for HTTP BASIC authentication for local development.

    This authentication method provides **zero security** and is **only**
    intended for local development. It is **not** suitable for production.

    The username takes a special form: ``username#role1,role2,...``. The roles
    are comma-separated and must be a subset of the roles supported by the
    application (see the source code). Any invalid roles are ignored.
    """
    if basic_credentials is None:
        return None
    username, _, roles_str = basic_credentials.username.partition("#")
    roles = {
        role.strip()
        for role in roles_str.split(",")
        if role.strip() in PERMISSION_MAP
    }
    user = User(name=username, roles=roles)
    AUTH_LOG.warning(
        "Development user acceped: %r with roles %r",
        user.name,
        user.roles,
    )
    return user


def _decode_token(jwt_secret: str, token: str) -> User | None:
    """Decode and validate a JWT, returning a User or None on failure."""
    try:
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        LOG.warning("Expired JWT token")
        return None
    except jwt.DecodeError:
        LOG.warning("Invalid JWT token")
        return None
    return User(
        name=decoded["username"],
        roles=set(decoded["roles"]),
    )


def get_token_user(
    config: Annotated[ConfigParser, Depends(default)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(Bearer)
    ],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User | None:
    """
    Authenticate via JWT.

    Checks, in order:
    1. ``Authorization: Bearer <token>`` header (for API clients / backward compat)
    2. ``access_token`` HttpOnly cookie (for browser sessions)
    """
    jwt_secret = config.get("security", "jwt_secret")

    # 1) Bearer header
    if credentials is not None and credentials.credentials:
        return _decode_token(jwt_secret, credentials.credentials)

    # 2) Cookie
    if access_token:
        return _decode_token(jwt_secret, access_token)

    return None


def get_optional_user(
    local_user: Annotated[User | None, Depends(local_dev_user)],
    token_user: Annotated[User | None, Depends(get_token_user)],
) -> User | None:
    return local_user or token_user or None


def get_user(
    optional_user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    if optional_user is None:
        raise AccessDenied(
            "Invalid or empty credentials (invalid or expired token maybe?)",
            AuthDeniedReason.NOT_AUTHENTICATED,
        )
    return optional_user


async def is_event_admin(
    session: AsyncSession, event_id: int, user: "User"
) -> bool:
    # Global admins (by role) are always event admins
    if "admin" in user.roles or user.name == "admin":
        return True
    query = select(EventUserRole).filter(
        and_(
            EventUserRole.event_id == event_id,
            EventUserRole.user_name == user.name,
            EventUserRole.role_name.in_(
                (EVENT_OWNER_ROLE, EVENT_CO_ADMIN_ROLE)
            ),
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def require_event_admin_user(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int = Path(),
) -> User:
    if await is_event_admin(session, event_id, auth_user):
        return auth_user
    raise AccessDenied(
        "Access denied (event admin or owner required)",
        reason=AuthDeniedReason.ACCESS_DENIED,
    )


async def require_event_mutation_access(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int = Path(),
) -> User:
    event_query = select(Event).filter_by(id=event_id)
    event = (await session.execute(event_query)).scalar_one_or_none()
    if not event:
        raise AccessDenied(
            "Unknown event",
            reason=AuthDeniedReason.ACCESS_DENIED,
        )

    # Event owners and co-admins may mutate outside the event window.
    if await is_event_admin(session, event_id, auth_user):
        return auth_user

    now = datetime.now(timezone.utc)
    # Check if now is within the event's time_range [start, end)
    # The Range object has .lower and .upper properties
    if event.time_range.lower <= now < event.time_range.upper:
        return auth_user

    raise AccessDenied(
        "Mutations are not allowed outside the event window",
        reason=AuthDeniedReason.ACCESS_DENIED,
    )
