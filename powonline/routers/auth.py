import logging
from configparser import ConfigParser
from time import time
from typing import Annotated

import httpx
import jwt
from authlib.integrations.starlette_client import OAuth
from authlib.jose import jwt
from authlib.oidc.discovery import get_well_known_url
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from powonline import core, model, schema
from powonline.auth import Bearer, User, confidential_oauth
from powonline.config import default
from powonline.dependencies import get_db
from powonline.exc import AccessDenied, AuthDeniedReason
from powonline.social import Social

ROUTER = APIRouter(prefix="", tags=["authentication"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/social-login/{provider}")
def social_login(
    config: Annotated[ConfigParser, Depends(default)], provider: str
):
    client = Social.create(config, provider)
    if not client:
        return "%s is not supported for login!" % provider
    authorization_url, state = client.process_login()
    # State is used to prevent CSRF, keep this for later.
    session["oauth_state"] = state
    return {"authorization_url": authorization_url}


@ROUTER.get("/connect/{provider}")
def callback(config: Annotated[ConfigParser, Depends(default)], provider):
    client = Social.create(config, provider)
    if not client:
        return "%s is not supported for login!" % provider
    user_info = client.get_user_info(session["oauth_state"], request.url)
    return jsonify(user_info)


@ROUTER.post("/login")
async def login(
    session: Annotated[AsyncSession, Depends(get_db)],
    config: Annotated[ConfigParser, Depends(default)],
    auth_data: schema.SocialCredentials | schema.PasswordCredentials = Body(),
):
    if isinstance(auth_data, schema.SocialCredentials):
        provider = auth_data.social_provider
        token = auth_data.token
        user_id = auth_data.user_id
        client = Social.create(config, provider)
        if not client:
            return (
                "Social provider %r not available (either not supported "
                "or not fully configured on the back-end)."
            ), 500
        user_info = client.get_user_info_simple(token)
        if user_info:
            user = await core.User.by_social_connection(
                session,
                provider,
                user_id,
                {
                    "display_name": user_info["name"],
                    "avatar_url": user_info["picture"],
                    "email": user_info.get("email"),
                },
            )
        else:
            raise AccessDenied(
                "Invalid social login",
                reason=AuthDeniedReason.NOT_AUTHENTICATED,
            )
    elif isinstance(auth_data, schema.PasswordCredentials):
        username = auth_data.username
        password = auth_data.password
        user = await model.User.get(session, username)
        if not user or not user.checkpw(password):
            raise AccessDenied(
                "Access Denied!",
                reason=AuthDeniedReason.NOT_AUTHENTICATED,
            )
    else:
        raise HTTPException(400, "Invalid request")

    if not user:
        raise AccessDenied(
            "Access Denied!",
            reason=AuthDeniedReason.NOT_AUTHENTICATED,
        )

    user_roles = await user.awaitable_attrs.roles
    roles = {role.name for role in user_roles or []}
    # JWT token expiration time (in seconds). Default: 2 hours
    jwt_lifetime = int(
        config.get("security", "jwt_lifetime", fallback=(2 * 60 * 60))
    )

    now = int(time())
    payload = {
        "username": user.name,
        "roles": list(roles),
        "iat": now,
        "exp": now + jwt_lifetime,
    }
    jwt_secret = config.get("security", "jwt_secret")
    result = {
        "token": jwt.encode(payload, jwt_secret),
        "roles": list(roles),  # convenience for the frontend
        "user": user.name,  # convenience for the frontend
    }
    return result


@ROUTER.post("/login/renew")
def renew_token(
    config: Annotated[ConfigParser, Depends(default)],
):
    data = request.get_json()
    current_token = data["token"]
    jwt_secret = config.get("security", "jwt_secret")
    # JWT token expiration time (in seconds). Default: 2 hours
    jwt_lifetime = int(
        config.get("security", "jwt_lifetime", fallback=(2 * 60 * 60))
    )
    try:
        token_info = jwt.decode(current_token, jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        LOG.debug("Renewal of invalid token: %s", exc)
        return "Invalid Token!", 400

    now = int(time())
    new_payload = {
        "username": token_info["username"],
        "roles": token_info["roles"],
        "iat": now,
        "exp": now + jwt_lifetime,
    }
    new_token = jwt.encode(new_payload, jwt_secret)
    return jsonify({"token": new_token})


@ROUTER.get("/dummy-request")
def dummy_request(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(Bearer)]
):
    if auth is None:
        raise HTTPException(401, "Unauthorized")
    # issuer = "http://idp:8080/realms/localdev"
    # issuer = "https://accounts.google.com/"
    issuer = "https://login.microsoftonline.com/b32ede06-d7e3-48f0-b82c-20fab650f67f/v2.0"
    wk_url = get_well_known_url(issuer, external=True)
    response = httpx.get(wk_url)
    jwks_uri = response.json().get("jwks_uri", "")
    response = httpx.get(jwks_uri)
    jwks = response.json()
    try:
        payload = jwt.decode(
            auth.credentials,
            key=jwks,
            claims_options={
                "iss": {
                    "essential": True,
                    "values": [
                        issuer,
                        "http://localhost:8080/realms/localdev",
                    ],
                }
            },
        )
        payload.validate(leeway=60)
    except Exception as exc:
        raise HTTPException(401, str(exc))


@ROUTER.get("/login/keycloak")
async def login_via_keycloak(
    request: Request, oauth: Annotated[OAuth, Depends(confidential_oauth)]
):
    keycloak = oauth.create_client("keycloak")
    if keycloak is None:
        raise HTTPException(500, "Keycloak not configured")
    redirect_uri = request.url_for("auth_via_keycloak")
    response = await keycloak.authorize_redirect(request, redirect_uri)
    return response


@ROUTER.get("/oidc-redirect")
async def auth_via_keycloak(
    request: Request, oauth: Annotated[OAuth, Depends(confidential_oauth)]
):
    keycloak = oauth.create_client("keycloak")
    if keycloak is None:
        raise HTTPException(500, "Keycloak not configured")
    token = await keycloak.authorize_access_token(request)
    print(token)
    user = token["userinfo"]
    return RedirectResponse(f"http://localhost:5173?email={user['email']}")
