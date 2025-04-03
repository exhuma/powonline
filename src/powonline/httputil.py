import logging
from typing import TYPE_CHECKING, cast

from flask import current_app, request
from flask.wrappers import Response

LOG = logging.getLogger(__name__)

DEFAULT_ALLOWED_ORIGINS = {"http://localhost:8080"}

if TYPE_CHECKING:
    from powonline.web import MyFlask


def add_cors_headers(response: Response) -> None:
    """
    Modifies *response* and adds CORS headers as defined in the app-config
    """
    app = cast("MyFlask", current_app)
    cfg_data = app.localconfig.get("app", "allowed_origins", fallback="")
    elements = {line.strip() for line in cfg_data.splitlines() if line.strip()}
    allowed_origins = elements or DEFAULT_ALLOWED_ORIGINS
    origin = request.headers.get("Origin", "")
    if current_app.debug and origin not in allowed_origins:
        LOG.info(
            "Application is in debug mode, auto-adding %s to allowed origins",
            origin,
        )
        allowed_origins.add(origin)
    LOG.debug("Allowed CORS origins: %r", allowed_origins)

    if origin in allowed_origins:
        response.headers.add("Access-Control-Allow-Origin", origin)
    elif origin:
        LOG.error("Unauthorized CORS request from %r", origin)

    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization"
    )
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
