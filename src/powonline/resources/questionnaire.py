import logging
from configparser import ConfigParser
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core
from powonline.config import default
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="", tags=["questionnaire"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/events/{event_id}/questionnaire-scores")
async def get_team_station_questionnaire(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
):
    # TODO this is a quick hack to get finished in time. This route should move
    # TODO Questionnaires should not be linked to stations
    #      This is a simplifcation for the UI for now: no manual selection of
    #      the questionnaire by users.
    output = await core.questionnaire_scores(session, event_id=event_id)
    return output
