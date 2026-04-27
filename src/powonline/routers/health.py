import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from powonline import __version__

ROUTER = APIRouter()


@ROUTER.get("/healthz", include_in_schema=True)
async def healthz() -> JSONResponse:
    """
    Health-check endpoint.

    Returns the application version and the Git commit SHA that was baked
    into the image at build time (``--build-arg COMMIT_SHA=<sha>``).
    Useful for verifying exactly which build is running in an environment.
    """
    return JSONResponse(
        {
            "status": "ok",
            "version": __version__,
            "commit_sha": os.environ.get("COMMIT_SHA", "unknown"),
        }
    )
