import logging
from configparser import ConfigParser
from functools import lru_cache
from typing import Annotated

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    OAuth2AuthorizationCodeBearer,
)
from pydantic import BaseModel

from powonline.config import default
from powonline.exc import AccessDenied, AuthDeniedReason

LOG = logging.getLogger(__name__)
AUTH_LOG = logging.getLogger("auth")

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


def confidential_oauth(
    config: Annotated[ConfigParser, Depends(default)]
) -> OAuth:
    oauth = OAuth()
    client_id = config.get("social:keycloak", "client_id", fallback="").strip()
    client_secret = config.get(
        "social:keycloak", "client_secret", fallback=""
    ).strip()
    if not all([client_id, client_secret]):
        raise ValueError("Missing client_id or client_secret")
    oauth.register(
        name="keycloak",
        server_metadata_url="http://idp:8080/realms/localdev/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        # access_token_url=config.get("oauth", "access_token_url"),
        # authorize_url=config.get("oauth", "authorize_url"),
        # client_kwargs={'scope': 'openid email profile'},
        client_kwargs={"scope": "openid"},
    )
    return oauth


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


def get_token_user(
    config: Annotated[ConfigParser, Depends(default)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(Bearer)],
) -> User | None:
    if credentials is None or credentials.credentials is None:
        return None
    jwt_secret = config.get("security", "jwt_secret")
    token = credentials.credentials
    try:
        decoded = jwt.decode(
            token, jwt_secret, algorithms=["HS256"], verify=True
        )
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
