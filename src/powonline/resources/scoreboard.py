import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/events/{event_id}/scoreboard", tags=["scoreboard"])
LOG = logging.getLogger(__name__)


@ROUTER.get("")
async def get(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
):
    output = await core.scoreboard(session, event_id=event_id)
    return list(output)
