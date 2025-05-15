import logging

from flask import Blueprint

from powonline import core

from .core import questionnaire_scores
from .model import DB

ROUTER = Blueprint("custom-routes", __name__)

LOG = logging.getLogger(__name__)


@ROUTER.delete("/questionnaire/<questionnaire_name>/station")
def unassign_questionnaire_from_station(questionnaire_name: str):
    output = questionnaire_scores(DB.session)

    success = core.Questionnaire.unassign_station(
        DB.session, questionnaire_name
    )
    if success:
        return "", 204
    else:
        return "Station is already assigned to that questionnaire", 400
