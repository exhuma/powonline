from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from powonline import error_handlers, resources, routers

app = FastAPI()


def create_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO
        allow_methods=["*"],  # TODO
        allow_headers=["*"],  # TODO
        allow_credentials=True,
    )
    # TODO auth
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
