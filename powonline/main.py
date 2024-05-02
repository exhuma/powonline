import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from powonline import error_handlers, resources, routers

LOG = logging.getLogger(__name__)
DEFAULT_ALLOWED_ORIGINS = {"http://localhost:8080"}


def get_cors_data() -> dict[str, list[str]]:
    # TODO cfg_data = app.localconfig.get("app", "allowed_origins", fallback="")
    allowed_origins = ["http://localhost:5173"]
    # TODO origin = request.headers.get("Origin", "")
    # TODO if current_app.debug and origin not in allowed_origins:
    # TODO     LOG.info(
    # TODO         "Application is in debug mode, auto-adding %s to allowed origins",
    # TODO         origin,
    # TODO     )
    # TODO     allowed_origins.add(origin)
    # TODO LOG.debug("Allowed CORS origins: %r", allowed_origins)

    # TODO if origin in allowed_origins:
    # TODO     response.headers.add("Access-Control-Allow-Origin", origin)
    # TODO elif origin:
    # TODO     LOG.error("Unauthorized CORS request from %r", origin)

    output: dict[str, list[str]] = {
        "allowed_origins": list(allowed_origins),
        "allowed_headers": ["Content-Type", "Authorization"],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
    }
    return output


def create_app():
    app = FastAPI()
    cors_info = get_cors_data()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_info["allowed_origins"],
        allow_methods=cors_info["allowed_methods"],
        allow_headers=cors_info["allowed_headers"],
        allow_credentials=True,
    )
    error_handlers.register(app)
    app.include_router(routers.app.ROUTER)
    app.include_router(routers.auth.ROUTER)
    app.include_router(resources.assignment.ROUTER)
    app.include_router(resources.audit.ROUTER)
    app.include_router(resources.dashboard.ROUTER)
    app.include_router(resources.job.ROUTER)
    app.include_router(resources.questionnaire.ROUTER)
    app.include_router(resources.route.ROUTER)
    app.include_router(resources.scoreboard.ROUTER)
    app.include_router(resources.station.ROUTER)
    app.include_router(resources.team.ROUTER)
    app.include_router(resources.upload.ROUTER)
    app.include_router(resources.user.ROUTER)
    return app
