from fastapi import APIRouter
from fastapi.responses import RedirectResponse

ROUTER = APIRouter()


@ROUTER.get("/")
async def root():
    """
    The main entry-point of the API (redirects to the docs)
    """
    return RedirectResponse("/docs")
