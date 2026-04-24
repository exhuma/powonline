import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from powonline import __version__, error_handlers, resources, routers
from powonline.config import default as get_config

LOG = logging.getLogger(__name__)


def _get_allowed_origins() -> list[str]:
    """
    Read ``allowed_origins`` from [app] in the config file.

    Falls back to ``["*"]`` when the key is absent or the config cannot be
    loaded (e.g. during unit tests that don't mount a real config file).
    """
    try:
        config = get_config()
        raw = config.get("app", "allowed_origins", fallback="*")
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        return origins or ["*"]
    except Exception:
        LOG.warning(
            "Could not read allowed_origins from config, defaulting to '*'"
        )
        return ["*"]


def create_app():
    app = FastAPI(title="powonline", version=__version__)
    allowed_origins = _get_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
    )
    error_handlers.register(app)
    app.include_router(routers.app.ROUTER)
    app.include_router(routers.auth.ROUTER)
    app.include_router(routers.legal.ROUTER)
    app.include_router(resources.assignment.ROUTER)
    app.include_router(resources.audit.ROUTER)
    app.include_router(resources.dashboard.ROUTER)
    app.include_router(resources.event.ROUTER)
    app.include_router(resources.event.DOMAIN_ROUTER)
    app.include_router(resources.job.ROUTER)
    app.include_router(resources.questionnaire.ROUTER)
    app.include_router(resources.route.ROUTER)
    app.include_router(resources.scoreboard.ROUTER)
    app.include_router(resources.sse.ROUTER)
    app.include_router(resources.station.ROUTER)
    app.include_router(resources.team.ROUTER)
    app.include_router(resources.upload.ROUTER)
    app.include_router(resources.user.ROUTER)
    return app
