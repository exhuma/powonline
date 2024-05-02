import logging
from configparser import ConfigParser
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
)

from powonline import schema
from powonline.auth import User
from powonline.config import default
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
def login(
    config: Annotated[ConfigParser, Depends(default)],
    auth_data: schema.SocialCredentials | schema.PasswordCredentials = Body(),
):
    user = None
    data = request.get_json()
    if "social_provider" in data:
        provider = data["social_provider"]
        token = data["token"]
        user_id = data["user_id"]
        client = Social.create(config, provider)
        if not client:
            return (
                "Social provider %r not available (either not supported "
                "or not fully configured on the back-end)."
            ), 500
        user_info = client.get_user_info_simple(token)
        if user_info:
            user = User.by_social_connection(
                DB.session,
                provider,
                user_id,
                {
                    "display_name": user_info["name"],
                    "avatar_url": user_info["picture"],
                    "email": user_info.get("email"),
                },
            )
        else:
            return "Access Denied", 401
    else:
        username = data["username"]
        password = data["password"]
        user = User.get(DB.session, username)
        if not user or not user.checkpw(password):
            return "Access Denied", 401

    if not user:
        return "Access Denied", 401

    roles = {role.name for role in user.roles or []}
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
    return jsonify(result)


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
