import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, require_event_admin_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/events/{event_id}", tags=["questionnaire"])
LOG = logging.getLogger(__name__)


@ROUTER.get("/questionnaire")
async def all_questionnaires(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
) -> schema.ListResult[schema.QuestionnaireSchema]:
    items = await core.Questionnaire.all(session, event_id=event_id)
    output = [schema.QuestionnaireSchema.model_validate(item) for item in items]
    return schema.ListResult(items=output)


@ROUTER.post("/questionnaire", status_code=201)
async def create_questionnaire(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    questionnaire: schema.QuestionnaireSchema = Body(),
) -> schema.QuestionnaireSchema:
    auth_user.require_permission("admin_stations")
    payload = questionnaire.model_dump()
    payload["event_id"] = event_id
    output = await core.Questionnaire.create_new(session, payload)
    return schema.QuestionnaireSchema.model_validate(output)


@ROUTER.put("/questionnaire/{name}")
async def update_questionnaire(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
    questionnaire: schema.QuestionnaireSchema = Body(),
) -> schema.QuestionnaireSchema:
    auth_user.require_permission("admin_stations")
    payload = questionnaire.model_dump()
    payload["event_id"] = event_id
    output = await core.Questionnaire.upsert(
        session,
        name,
        payload,
        event_id=event_id,
    )
    return schema.QuestionnaireSchema.model_validate(output)


@ROUTER.delete("/questionnaire/{name}")
async def delete_questionnaire(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    name: str,
) -> Response:
    auth_user.require_permission("admin_stations")
    await core.Questionnaire.delete(session, name, event_id=event_id)
    return Response(None, 204)


@ROUTER.post("/station/{station_name}/questionnaires")
async def assign_questionnaire_to_station(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    station_name: str,
    questionnaire: schema.QuestionnaireSchema = Body(),
) -> Response:
    auth_user.require_permission("admin_stations")
    success = await core.Questionnaire.assign_station(
        session,
        station_name,
        questionnaire.name,
        event_id=event_id,
    )
    if success:
        return Response(None, 204)
    return JSONResponse("Unknown station or questionnaire for event", 404)


@ROUTER.delete("/questionnaire/{questionnaire_name}/station")
async def unassign_questionnaire_from_station(
    auth_user: Annotated[User, Depends(require_event_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    questionnaire_name: str,
) -> Response:
    auth_user.require_permission("admin_stations")
    success = await core.Questionnaire.unassign_station(
        session,
        questionnaire_name,
        event_id=event_id,
    )
    if success:
        return Response(None, 204)
    return JSONResponse("Unknown questionnaire for event", 404)


@ROUTER.get("/questionnaire-scores")
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
