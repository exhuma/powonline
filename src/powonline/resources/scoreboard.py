import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/scoreboard", tags=["scoreboard"])
LOG = logging.getLogger(__name__)


@ROUTER.get("")
async def get(
    session: Annotated[AsyncSession, Depends(get_db)],
):
    output = await core.scoreboard(session)
    output = make_response(dumps(output, cls=MyJsonEncoder), 200)
    output.content_type = "application/json"
    return output
