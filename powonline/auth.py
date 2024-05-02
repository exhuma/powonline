import logging
from configparser import ConfigParser
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from powonline.config import default
from powonline.exc import AccessDenied

LOG = logging.getLogger(__name__)

PERMISSION_MAP = {
    "admin": {
        "admin_files",
        "admin_routes",
        "admin_stations",
        "admin_teams",
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
}

Bearer = HTTPBearer()


class User(BaseModel):
    name: str
    roles: set[str]

    @property
    def permissions(self) -> set[str]:
        LOG.debug("Bearer token with the following roles: %r", self.roles)
        all_permissions = set()
        for role in self.roles:
            all_permissions |= PERMISSION_MAP.get(role, set())

        LOG.debug(
            "Bearer token grants the following permissions: %r", all_permissions
        )
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


def get_user(
    config: Annotated[ConfigParser, Depends(default)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(Bearer)],
) -> User:
    token = credentials.credentials
    jwt_secret = config.get("security", "jwt_secret")
    try:
        auth_payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
    except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError):
        LOG.info("Bearer token seems to have been tampered with!")
        raise AccessDenied("Access Denied (invalid token)!")
    print(auth_payload)
    return User(name="admin", roles={"admin"})  # XXX This is a fake
