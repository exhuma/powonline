# TODO: This file is badly named. It no longer shims between FastAPI and the
#       db.
import json
import logging
from pathlib import Path
from typing import Annotated

from authlib.jose import JWTClaims
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from flightlogs.auth.kiosk import kiosk_is_valid, make_kiosk_user
from flightlogs.auth.msal import (
    AuthError,
    OAuth2AuthorizationCodeBearerWithDiscovery,
)
from flightlogs.dependencies import get_persistence, get_settings
from flightlogs.model.auth import (
    ROLE_PERMISSIONS,
    DefinedRole,
    Permission,
    Role,
    User,
)
from flightlogs.persistence.types import Storage
from flightlogs.settings import Settings

LOG = logging.getLogger(__name__)
AUTH_LOG = logging.getLogger("auth")

LOCAL_AUTH = HTTPBasic(
    auto_error=False, description="Authentication for local-development"
)
ENTRA_ID_TOKEN = OAuth2AuthorizationCodeBearerWithDiscovery(
    authorizationUrl="auth",
    tokenUrl="token",
    optional=True,
    description="Authentication for Microsoft Identity Platform",
)


def local_dev_user(
    basic_credentials: Annotated[
        HTTPBasicCredentials | None, Depends(LOCAL_AUTH)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    if basic_credentials is None:
        return None
    dev_auth_file = Path(settings.dev_auth_file)
    if not settings.dev_auth_file.strip():
        AUTH_LOG.warning("No development authentication file specified")
        return None
    if not dev_auth_file.exists():
        AUTH_LOG.warning(
            "Development authentication file %s not found", dev_auth_file
        )
        return None
    data = json.loads(dev_auth_file.read_text())
    user_details = data.get(basic_credentials.username, None)
    if user_details is None:
        AUTH_LOG.warning(
            "User %r not found in development authentication file",
            basic_credentials.username,
        )
        return None
    roles_str: list[str] = user_details.get("roles", [])
    permissions: frozenset[Permission] = frozenset()
    for role in roles_str:
        permissions |= frozenset(ROLE_PERMISSIONS.get(DefinedRole(role), []))
    user = User(
        id=user_details.get("id", "unknown"),
        display_name=user_details.get("display_name", "unknown"),
        roles=frozenset(
            Role(name=DefinedRole(role_name)) for role_name in roles_str
        ),
        permissions=permissions,
    )
    return user


async def get_optional_user(
    jwt_claims: Annotated[JWTClaims | None, Depends(ENTRA_ID_TOKEN)],
    basic_user: Annotated[User | None, Depends(local_dev_user)],
    persistence: Annotated[Storage, Depends(get_persistence)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    if basic_user:
        AUTH_LOG.debug(
            "User %r detected via BASIC auth", basic_user.display_name
        )
        return basic_user
    if jwt_claims is None:
        AUTH_LOG.debug("Neither BASIC nor JWT auth detected")
        return None
    if jwt_claims.get("token-type", "") == "kiosk":
        AUTH_LOG.debug("Kiosk %r detected", jwt_claims.get("kiosk-name"))
        if not kiosk_is_valid(persistence, jwt_claims.get("kiosk-id", "")):
            AUTH_LOG.debug(
                "Access from invalidated kiosk %r",
                jwt_claims.get("kiosk-name"),
            )
            return None
        return make_kiosk_user(
            jwt_claims["kiosk-id"], jwt_claims.get("kiosk-name", "")
        )
    output = persistence.ensure_user_exists(jwt_claims)
    email = jwt_claims.get("preferred_username", "").strip()
    if settings.admin_email:
        if not email:
            LOG.warning(
                "Admin e-mail is set, but the JWT claim did not contain the "
                "field 'preferred_username' or it was empty."
            )
        if email == settings.admin_email:
            output = output.model_copy(
                update={"permissions": frozenset(list(Permission))}
            )
            LOG.debug(
                "Overriding user-permissions. Granting all permissions because "
                "this user matches the current 'admin_email' setting",
            )
    return output


async def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)]
) -> User:
    if user is None:
        raise AuthError("Access Denied", status_code=401)
    return user
