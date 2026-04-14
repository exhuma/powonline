"""
Tests for the /auth/* endpoints.

Strategy
--------
- ``POST /auth/login``  — mock model.User.get + checkpw to avoid bcrypt/DB
- ``GET  /auth/me``     — override get_user dep (same pattern as other test files)
- ``POST /auth/refresh`` — craft a real refresh JWT, send as cookie
- ``POST /auth/logout``  — check that cookies are cleared
- ``GET  /auth/providers`` — override config dep to return a minimal config
- OAuth PKCE endpoints are tested at the happy-path HTTP level only (no real
  IdP calls): social_login_start is tested to verify redirect + cookie; the
  callback is tested with a mocked Social client.
"""

import asyncio
import logging
from configparser import ConfigParser
from textwrap import dedent
from time import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from powonline.auth import User, get_user
from powonline.config import default as config_default

LOG = logging.getLogger(__name__)

JWT_SECRET = "testing-secret-key-long-enough-for-hs256"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(extra: str = "") -> ConfigParser:
    """Build a minimal test ConfigParser with the correct jwt_secret."""
    cfg = ConfigParser()
    cfg.read_string(
        dedent(
            f"""\
            [security]
            jwt_secret = {JWT_SECRET}
            {extra}
            """
        )
    )
    return cfg


def _make_refresh_token(username: str, roles: list[str]) -> str:
    now = int(time())
    payload = {
        "sub": username,
        "username": username,
        "roles": roles,
        "iat": now,
        "exp": now + 7 * 24 * 3600,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _make_access_token(username: str, roles: list[str]) -> str:
    now = int(time())
    payload = {
        "sub": username,
        "username": username,
        "roles": roles,
        "iat": now,
        "exp": now + 15 * 60,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _expired_token(username: str) -> str:
    payload = {
        "sub": username,
        "username": username,
        "roles": [],
        "iat": int(time()) - 9999,
        "exp": int(time()) - 9000,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


async def test_login_success(app: FastAPI, test_client: AsyncClient, seed):
    """Valid credentials → 200 + access_token and refresh_token cookies."""
    app.dependency_overrides[config_default] = lambda: _make_config()

    mock_user = MagicMock()
    mock_user.name = "user-red"
    mock_user.checkpw.return_value = True
    # awaitable_attrs.roles is accessed as `await user_orm.awaitable_attrs.roles`
    # This means awaitable_attrs.roles must be a directly awaitable object.
    fut: asyncio.Future = asyncio.get_event_loop().create_future()
    fut.set_result([])
    mock_user.awaitable_attrs = MagicMock()
    mock_user.awaitable_attrs.roles = fut

    try:
        with patch(
            "powonline.routers.auth.model.User.get",
            new=AsyncMock(return_value=mock_user),
        ):
            response = await test_client.post(
                "/auth/login",
                json={"username": "user-red", "password": "user-red"},
            )

        assert response.status_code == 200, response.content
        data = response.json()
        assert data["user"] == "user-red"
        assert "roles" in data
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    finally:
        app.dependency_overrides.pop(config_default, None)


async def test_login_wrong_password(app: FastAPI, test_client: AsyncClient, seed):
    """Wrong password → 401 (NOT_AUTHENTICATED reason)."""
    app.dependency_overrides[config_default] = lambda: _make_config()

    mock_user = MagicMock()
    mock_user.name = "user-red"
    mock_user.checkpw.return_value = False

    try:
        with patch(
            "powonline.routers.auth.model.User.get",
            new=AsyncMock(return_value=mock_user),
        ):
            response = await test_client.post(
                "/auth/login",
                json={"username": "user-red", "password": "wrong"},
            )

        assert response.status_code == 401, response.content
    finally:
        app.dependency_overrides.pop(config_default, None)


async def test_login_unknown_user(app: FastAPI, test_client: AsyncClient, seed):
    """Unknown user → 401."""
    app.dependency_overrides[config_default] = lambda: _make_config()

    try:
        with patch(
            "powonline.routers.auth.model.User.get",
            new=AsyncMock(return_value=None),
        ):
            response = await test_client.post(
                "/auth/login",
                json={"username": "nobody", "password": "whatever"},
            )

        assert response.status_code == 401, response.content
    finally:
        app.dependency_overrides.pop(config_default, None)


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


async def test_me_authenticated(app: FastAPI, test_client: AsyncClient, seed):
    """Authenticated user → 200 with user + roles."""
    app.dependency_overrides[get_user] = lambda: User(name="user-red", roles={"admin"})
    try:
        response = await test_client.get("/auth/me")
        assert response.status_code == 200, response.content
        data = response.json()
        assert data["user"] == "user-red"
        assert "admin" in data["roles"]
    finally:
        app.dependency_overrides.pop(get_user, None)


async def test_me_unauthenticated(test_client: AsyncClient):
    """No cookie / no token → 401."""
    response = await test_client.get("/auth/me")
    assert response.status_code == 401, response.content


async def test_me_with_access_cookie(app: FastAPI, test_client: AsyncClient, seed):
    """Valid access_token cookie → 200."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    token = _make_access_token("user-red", ["admin"])
    test_client.cookies.set("access_token", token)
    try:
        response = await test_client.get("/auth/me")
        assert response.status_code == 200, response.content
        data = response.json()
        assert data["user"] == "user-red"
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


async def test_refresh_success(app: FastAPI, test_client: AsyncClient):
    """Valid refresh cookie → 200 + new access_token cookie."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    token = _make_refresh_token("user-red", ["admin"])
    test_client.cookies.set("refresh_token", token)
    try:
        response = await test_client.post("/auth/refresh")
        assert response.status_code == 200, response.content
        data = response.json()
        assert data["user"] == "user-red"
        assert "access_token" in response.cookies
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


async def test_refresh_no_cookie(test_client: AsyncClient):
    """No refresh cookie → 401."""
    response = await test_client.post("/auth/refresh")
    assert response.status_code == 401, response.content


async def test_refresh_expired_token(app: FastAPI, test_client: AsyncClient):
    """Expired refresh token → 401."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    token = _expired_token("user-red")
    test_client.cookies.set("refresh_token", token)
    try:
        response = await test_client.post("/auth/refresh")
        assert response.status_code == 401, response.content
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


async def test_refresh_wrong_token_type(app: FastAPI, test_client: AsyncClient):
    """Access token sent as refresh cookie → 401 (wrong type)."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    # An access token has type="access", not "refresh"
    token = _make_access_token("user-red", ["admin"])
    test_client.cookies.set("refresh_token", token)
    try:
        response = await test_client.post("/auth/refresh")
        assert response.status_code == 401, response.content
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


async def test_refresh_invalid_token(app: FastAPI, test_client: AsyncClient):
    """Garbage token → 401."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    test_client.cookies.set("refresh_token", "not.a.jwt")
    try:
        response = await test_client.post("/auth/refresh")
        assert response.status_code == 401, response.content
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


async def test_logout_clears_cookies(test_client: AsyncClient):
    """Logout clears access_token and refresh_token cookies."""
    response = await test_client.post("/auth/logout")
    assert response.status_code == 200, response.content
    data = response.json()
    assert data.get("ok") is True
    # Cookies should be deleted (set to empty / max-age=0)
    set_cookie_headers = response.headers.get_list("set-cookie")
    deleted = {h for h in set_cookie_headers if "max-age=0" in h.lower()}
    cookie_names_deleted = {h.split("=")[0].strip() for h in deleted}
    assert "access_token" in cookie_names_deleted
    assert "refresh_token" in cookie_names_deleted


# ---------------------------------------------------------------------------
# GET /auth/providers
# ---------------------------------------------------------------------------


async def test_providers_returns_empty_list_when_unconfigured(
    app: FastAPI, test_client: AsyncClient
):
    """Without any social provider sections, returns an empty list."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    try:
        response = await test_client.get("/auth/providers")
        assert response.status_code == 200, response.content
        data = response.json()
        assert isinstance(data, list)
        assert data == []
    finally:
        app.dependency_overrides.pop(config_default, None)


async def test_providers_returns_configured_provider(
    app: FastAPI, test_client: AsyncClient
):
    """When a provider section is configured, it appears in the list."""
    # Config section name uses colon separator: social:github
    cfg = _make_config(
        extra=dedent(
            """\
            [social:github]
            client_id = gh-client-id
            client_secret = gh-client-secret
            """
        )
    )
    app.dependency_overrides[config_default] = lambda: cfg
    try:
        response = await test_client.get("/auth/providers")
        assert response.status_code == 200, response.content
        data = response.json()
        assert isinstance(data, list)
        names = [p["name"] for p in data]
        assert "github" in names
    finally:
        app.dependency_overrides.pop(config_default, None)


# ---------------------------------------------------------------------------
# GET /auth/social/{provider}  (PKCE start)
# ---------------------------------------------------------------------------


async def test_social_login_start_unknown_provider(
    app: FastAPI, test_client: AsyncClient
):
    """Unknown/unconfigured provider → 400."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    try:
        response = await test_client.get(
            "/auth/social/nonexistent",
            params={"redirect_uri": "http://localhost/auth/callback/nonexistent"},
            follow_redirects=False,
        )
        assert response.status_code == 400, response.content
    finally:
        app.dependency_overrides.pop(config_default, None)


async def test_social_login_start_redirects(app: FastAPI, test_client: AsyncClient):
    """
    Known provider → 302 redirect to IdP authorization URL + pkce_state cookie.
    The Social.create call and the underlying authorization_url are mocked.
    """
    cfg = _make_config(
        extra=dedent(
            """\
            [social:github]
            client_id = gh-client-id
            client_secret = gh-client-secret
            """
        )
    )
    app.dependency_overrides[config_default] = lambda: cfg

    mock_client = MagicMock()
    mock_client.authorization_url = MagicMock(
        return_value="https://github.com/login/oauth/authorize?state=x"
    )

    try:
        with patch("powonline.routers.auth.Social.create", return_value=mock_client):
            response = await test_client.get(
                "/auth/social/github",
                params={"redirect_uri": "http://localhost/auth/callback/github"},
                follow_redirects=False,
            )
        assert response.status_code == 302, response.content
        assert "github.com" in response.headers["location"]
        assert "pkce_state" in response.cookies
    finally:
        app.dependency_overrides.pop(config_default, None)


# ---------------------------------------------------------------------------
# GET /auth/callback/{provider}
# ---------------------------------------------------------------------------


async def test_callback_missing_pkce_cookie(
    app: FastAPI, test_client: AsyncClient, seed
):
    """No pkce_state cookie → 400."""
    response = await test_client.get(
        "/auth/callback/github",
        params={
            "code": "somecode",
            "state": "somestate",
            "redirect_uri": "http://localhost/auth/callback/github",
            "frontend_url": "http://localhost/",
        },
        follow_redirects=False,
    )
    assert response.status_code == 400, response.content


async def test_callback_state_mismatch(app: FastAPI, test_client: AsyncClient, seed):
    """State in query param doesn't match pkce cookie → 400."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    pkce_payload = {
        "state": "correct-state",
        "cv": "code-verifier",
        "provider": "github",
        "iat": int(time()),
        "exp": int(time()) + 600,
    }
    pkce_cookie = jwt.encode(pkce_payload, JWT_SECRET, algorithm="HS256")
    test_client.cookies.set("pkce_state", pkce_cookie)
    try:
        response = await test_client.get(
            "/auth/callback/github",
            params={
                "code": "somecode",
                "state": "wrong-state",  # mismatch
                "redirect_uri": "http://localhost/auth/callback/github",
                "frontend_url": "http://localhost/",
            },
            follow_redirects=False,
        )
        assert response.status_code == 400, response.content
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


async def test_callback_provider_mismatch(app: FastAPI, test_client: AsyncClient, seed):
    """Provider in URL doesn't match pkce cookie → 400."""
    app.dependency_overrides[config_default] = lambda: _make_config()
    pkce_payload = {
        "state": "my-state",
        "cv": "code-verifier",
        "provider": "google",  # cookie says google
        "iat": int(time()),
        "exp": int(time()) + 600,
    }
    pkce_cookie = jwt.encode(pkce_payload, JWT_SECRET, algorithm="HS256")
    test_client.cookies.set("pkce_state", pkce_cookie)
    try:
        response = await test_client.get(
            "/auth/callback/github",  # URL says github — mismatch
            params={
                "code": "somecode",
                "state": "my-state",
                "redirect_uri": "http://localhost/auth/callback/github",
                "frontend_url": "http://localhost/",
            },
            follow_redirects=False,
        )
        assert response.status_code == 400, response.content
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)


async def test_callback_success(app: FastAPI, test_client: AsyncClient, seed):
    """
    Happy path: valid pkce cookie, matching state/provider, mocked Social
    client returns token + user info → 302 to frontend_url with auth cookies.
    """
    app.dependency_overrides[config_default] = lambda: _make_config(
        extra=dedent(
            """\
            [social:github]
            client_id = gh-client-id
            client_secret = gh-client-secret
            """
        )
    )

    pkce_payload = {
        "state": "good-state",
        "cv": "code-verifier",
        "provider": "github",
        "iat": int(time()),
        "exp": int(time()) + 600,
    }
    pkce_cookie = jwt.encode(pkce_payload, JWT_SECRET, algorithm="HS256")
    test_client.cookies.set("pkce_state", pkce_cookie)

    mock_social = MagicMock()
    mock_social.exchange_code = MagicMock(
        return_value={"access_token": "gh-access-token"}
    )
    mock_social.get_user_info = MagicMock(
        return_value={"email": "newuser@example.com", "name": "New User"}
    )

    try:
        with patch("powonline.routers.auth.Social.create", return_value=mock_social):
            response = await test_client.get(
                "/auth/callback/github",
                params={
                    "code": "somecode",
                    "state": "good-state",
                    "redirect_uri": "http://localhost/auth/callback/github",
                    "frontend_url": "http://localhost/",
                },
                follow_redirects=False,
            )
        assert response.status_code == 302, response.content
        assert response.headers["location"] == "http://localhost/"
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    finally:
        test_client.cookies.clear()
        app.dependency_overrides.pop(config_default, None)
