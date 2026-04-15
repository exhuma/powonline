"""
Authentication router.

Endpoints
---------
POST  /auth/login                   Password login → set access + refresh cookies
GET   /auth/providers               List configured OAuth providers
GET   /auth/social/{provider}       Start OAuth2 PKCE flow → redirect to IdP
GET   /auth/callback/{provider}     OAuth2 callback → set cookies → redirect to frontend
POST  /auth/refresh                 Rotate access cookie using refresh cookie
POST  /auth/logout                  Clear both cookies
GET   /auth/me                      Return current session info (user + roles)

Cookie strategy
---------------
access_token  HttpOnly Secure SameSite=None  15 min   read by every endpoint
refresh_token HttpOnly Secure SameSite=None  7 days   read only by /auth/refresh
pkce_state    HttpOnly Secure SameSite=None  10 min   carries state+verifier across redirect

All tokens are HS256 JWTs signed with jwt_secret from config [security].
"""

import hashlib
import hmac
import inspect
import logging
import os
import secrets
from base64 import urlsafe_b64encode
from configparser import ConfigParser
from time import time
from typing import Annotated

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, model, schema
from powonline.auth import User, get_user
from powonline.config import default
from powonline.dependencies import get_db
from powonline.exc import AccessDenied, AuthDeniedReason
from powonline.social import Social

ROUTER = APIRouter(prefix="/auth", tags=["authentication"])
LOG = logging.getLogger(__name__)

# Lifetimes in seconds
ACCESS_TOKEN_LIFETIME = 15 * 60  # 15 minutes
REFRESH_TOKEN_LIFETIME = 7 * 24 * 3600  # 7 days
PKCE_STATE_LIFETIME = 10 * 60  # 10 minutes

# Set POWONLINE_INSECURE_COOKIES=1 for local HTTP dev (disables Secure + SameSite=None)
_INSECURE = bool(int(os.environ.get("POWONLINE_INSECURE_COOKIES", "0")))
_COOKIE_SECURE = not _INSECURE
_COOKIE_SAMESITE = "lax" if _INSECURE else "none"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cookie_kwargs(max_age: int) -> dict:
    return dict(
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=max_age,
    )


def _make_access_token(jwt_secret: str, username: str, roles: list[str]) -> str:
    now = int(time())
    payload = {
        "sub": username,
        # Keep legacy "username" claim for backward compat with auth.py
        "username": username,
        "roles": roles,
        "iat": now,
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "type": "access",
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def _make_refresh_token(jwt_secret: str, username: str, roles: list[str]) -> str:
    now = int(time())
    payload = {
        "sub": username,
        "username": username,
        "roles": roles,
        "iat": now,
        "exp": now + REFRESH_TOKEN_LIFETIME,
        "type": "refresh",
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def _make_pkce_state_token(
    jwt_secret: str,
    state: str,
    code_verifier: str,
    provider: str,
    redirect_uri: str,
    frontend_url: str,
) -> str:
    now = int(time())
    payload = {
        "state": state,
        "cv": code_verifier,
        "provider": provider,
        "redirect_uri": redirect_uri,
        "frontend_url": frontend_url,
        "iat": now,
        "exp": now + PKCE_STATE_LIFETIME,
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return urlsafe_b64encode(digest).rstrip(b"=").decode()


def _set_auth_cookies(
    response: Response, jwt_secret: str, username: str, roles: list[str]
) -> None:
    access = _make_access_token(jwt_secret, username, roles)
    refresh = _make_refresh_token(jwt_secret, username, roles)
    response.set_cookie("access_token", access, **_cookie_kwargs(ACCESS_TOKEN_LIFETIME))
    response.set_cookie(
        "refresh_token", refresh, **_cookie_kwargs(REFRESH_TOKEN_LIFETIME)
    )


def _clear_auth_cookies(response: Response) -> None:
    kw = dict(httponly=True, secure=_COOKIE_SECURE, samesite=_COOKIE_SAMESITE)
    response.delete_cookie("access_token", **kw)
    response.delete_cookie("refresh_token", **kw)


async def _user_roles(db: AsyncSession, user_orm: model.User) -> list[str]:
    user_roles = await user_orm.awaitable_attrs.roles
    return [role.name for role in (user_roles or [])]


async def _call(fn, *args, **kwargs):
    """Call fn whether it is async or sync."""
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@ROUTER.get("/providers", response_model=list[schema.AuthProvider])
async def list_providers(
    config: Annotated[ConfigParser, Depends(default)],
):
    """Return the list of configured OAuth identity providers."""
    return Social.available_providers(config)


@ROUTER.post("/login", response_model=schema.SessionInfo)
async def login(
    body: schema.PasswordCredentials,
    db: Annotated[AsyncSession, Depends(get_db)],
    config: Annotated[ConfigParser, Depends(default)],
):
    """Password login. Sets access + refresh cookies on success."""
    user_orm = await model.User.get(db, body.username)
    if not user_orm or not user_orm.checkpw(body.password):
        raise AccessDenied(
            "Invalid credentials",
            reason=AuthDeniedReason.NOT_AUTHENTICATED,
        )

    jwt_secret = config.get("security", "jwt_secret")
    roles = await _user_roles(db, user_orm)

    response = JSONResponse({"user": user_orm.name, "roles": roles})
    _set_auth_cookies(response, jwt_secret, user_orm.name, roles)
    return response


@ROUTER.get("/social/{provider}")
async def social_login_start(
    provider: str,
    config: Annotated[ConfigParser, Depends(default)],
    redirect_uri: str = Query(
        ..., description="Backend callback URL the IdP should redirect to"
    ),
    frontend_url: str = Query(
        ..., description="Frontend URL to redirect to after successful login"
    ),
):
    """
    Begin an OAuth2 PKCE flow.

    Redirects the browser to the identity provider's authorization endpoint.
    A signed pkce_state cookie is set to carry state + code_verifier across
    the redirect without server-side session storage.
    """
    client = Social.create(config, provider)
    if client is None:
        raise HTTPException(400, f"Provider {provider!r} is not configured")

    jwt_secret = config.get("security", "jwt_secret")

    code_verifier = secrets.token_urlsafe(64)
    code_challenge = _pkce_challenge(code_verifier)
    state = secrets.token_urlsafe(32)

    auth_url = await _call(
        client.authorization_url, redirect_uri, state, code_challenge
    )

    pkce_cookie = _make_pkce_state_token(
        jwt_secret,
        state,
        code_verifier,
        provider,
        redirect_uri,
        frontend_url,
    )

    response = RedirectResponse(auth_url, status_code=302)
    response.set_cookie(
        "pkce_state", pkce_cookie, **_cookie_kwargs(PKCE_STATE_LIFETIME)
    )
    return response


@ROUTER.get("/callback/{provider}")
async def social_login_callback(
    provider: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    config: Annotated[ConfigParser, Depends(default)],
    code: str = Query(...),
    state: str = Query(...),
    redirect_uri: str | None = Query(
        None,
        description=(
            "Optional override of the callback URI; defaults to the URI used "
            "to start the flow"
        ),
    ),
    frontend_url: str | None = Query(
        None,
        description=(
            "Optional override of frontend redirect URL; defaults to the URL "
            "used to start the flow"
        ),
    ),
    pkce_state: Annotated[str | None, Cookie()] = None,
):
    """
    OAuth2 authorization code callback.

    Verifies state + PKCE, exchanges the code for an access token, fetches
    user info from the IdP, finds or creates the local user, then redirects
    to the frontend with auth cookies set.
    """
    if pkce_state is None:
        raise HTTPException(400, "Missing PKCE state cookie")

    jwt_secret = config.get("security", "jwt_secret")

    try:
        pkce = jwt.decode(pkce_state, jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            400, "PKCE state cookie expired — please try logging in again"
        )
    except jwt.DecodeError:
        raise HTTPException(400, "Invalid PKCE state cookie")

    if not hmac.compare_digest(pkce["state"], state):
        raise HTTPException(400, "State mismatch — possible CSRF attack")

    if pkce["provider"] != provider:
        raise HTTPException(400, "Provider mismatch in PKCE state")

    redirect_uri = redirect_uri or pkce.get("redirect_uri")
    frontend_url = frontend_url or pkce.get("frontend_url")
    if not redirect_uri:
        raise HTTPException(400, "Missing redirect_uri for token exchange")
    if not frontend_url:
        raise HTTPException(400, "Missing frontend_url for final redirect")

    code_verifier = pkce["cv"]

    client = Social.create(config, provider)
    if client is None:
        raise HTTPException(400, f"Provider {provider!r} is not configured")

    # Exchange code for tokens
    try:
        token_data = await _call(
            client.exchange_code, code, redirect_uri, code_verifier
        )
    except Exception as exc:
        LOG.error("Token exchange failed for %s: %s", provider, exc)
        raise HTTPException(502, "Token exchange with identity provider failed")

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(502, "No access token received from identity provider")

    # Fetch user info
    try:
        user_info = await _call(client.get_user_info, access_token)
    except Exception as exc:
        LOG.error("User info fetch failed for %s: %s", provider, exc)
        raise HTTPException(502, "Failed to retrieve user info from identity provider")

    # Find or create local user
    user_orm = await core.User.by_social_connection(
        db,
        provider,
        user_info.get("email") or user_info.get("name", "unknown"),
        {
            "display_name": user_info.get("name", ""),
            "avatar_url": user_info.get("picture", ""),
            "email": user_info.get("email", ""),
        },
    )

    roles = await _user_roles(db, user_orm)

    response = RedirectResponse(frontend_url, status_code=302)
    _set_auth_cookies(response, jwt_secret, user_orm.name, roles)
    # Remove the one-time PKCE state cookie
    response.delete_cookie(
        "pkce_state",
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
    )
    return response


@ROUTER.post("/refresh", response_model=schema.SessionInfo)
async def refresh(
    config: Annotated[ConfigParser, Depends(default)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    """
    Issue a new access cookie using the long-lived refresh cookie.
    Returns 401 if the refresh token is missing or expired.
    """
    if not refresh_token:
        raise HTTPException(401, "No refresh token")

    jwt_secret = config.get("security", "jwt_secret")
    try:
        payload = jwt.decode(refresh_token, jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired")
    except jwt.DecodeError:
        raise HTTPException(401, "Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")

    username = payload["username"]
    roles = payload["roles"]

    new_access = _make_access_token(jwt_secret, username, roles)
    response = JSONResponse({"user": username, "roles": roles})
    response.set_cookie(
        "access_token", new_access, **_cookie_kwargs(ACCESS_TOKEN_LIFETIME)
    )
    return response


@ROUTER.post("/logout")
async def logout():
    """Clear both auth cookies."""
    response = JSONResponse({"ok": True})
    _clear_auth_cookies(response)
    return response


@ROUTER.get("/me", response_model=schema.SessionInfo)
async def me(user: Annotated[User, Depends(get_user)]):
    """Return current session info. 401 if not authenticated."""
    return {"user": user.name, "roles": list(user.roles)}
