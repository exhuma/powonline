import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, get_user
from powonline.dependencies import get_db, get_pusher
from powonline.exc import (
    AccessDenied,
    AuthDeniedReason,
    NoQuestionnaireForStation,
)
from powonline.pusher import PusherWrapper

ROUTER = APIRouter(prefix="/job", tags=["job"])
LOG = logging.getLogger(__name__)


def validate_score(value):
    if isinstance(value, str):
        score = int(value, 10) if value.strip() else 0
    else:
        score = value if value else 0
    return score


async def _action_advance(
    session: AsyncSession,
    username: str,
    permissions: set[str],
    pusher: PusherWrapper,
    args: dict[str, Any],
) -> dict[str, Any]:
    station_name = args["station_name"]
    team_name = args["team_name"]

    has_access = await core.User.may_access_station(
        session, username, station_name
    )
    if "admin_stations" in permissions or (
        "manage_station" in permissions and has_access
    ):
        new_state = await core.Team.advance_on_station(
            session, team_name, station_name
        )
        output = {"result": {"state": new_state.value}}
        pusher.send_team_event(
            "state-change",
            {
                "station": station_name,
                "team": team_name,
                "new_state": new_state.value,
            },
        )
        return output
    raise AccessDenied("Access denied to this station!")


async def _action_set_score(
    session: AsyncSession,
    username: str,
    permissions: set[str],
    pusher: PusherWrapper,
    args: dict[str, Any],
) -> dict[str, Any]:
    station_name = args["station_name"]
    team_name = args["team_name"]
    score = validate_score(args["score"])

    has_access = await core.User.may_access_station(
        session, username, station_name
    )
    if "admin_stations" in permissions or (
        "manage_station" in permissions and has_access
    ):
        LOG.info(
            "Setting score of %s on %s to %s (by user: %s)",
            team_name,
            station_name,
            score,
            username,
        )
        old_score, new_score = await core.Team.set_station_score(
            session, team_name, station_name, score
        )
        if old_score != new_score:
            core.add_audit_log(
                session,
                username,
                schema.AuditType.STATION_SCORE,
                "Change score of team %r from %s to %s on station %s"
                % (team_name, old_score, score, station_name),
            )
        output = {
            "new_score": new_score,
        }
        pusher.send_team_event(
            "score-change",
            {
                "station": station_name,
                "team": team_name,
                "new_score": new_score,
            },
        )
        return output
    raise AccessDenied(
        "Access denied to this station!", reason=AuthDeniedReason.ACCESS_DENIED
    )


async def _action_set_questionnaire_score(
    session: AsyncSession,
    username: str,
    permissions: set[str],
    pusher: PusherWrapper,
    args: dict[str, Any],
) -> dict[str, Any]:
    station_name = args["station_name"]
    team_name = args["team_name"]
    score = validate_score(args["score"])

    has_access = await core.User.may_access_station(
        session, username, station_name
    )
    if "admin_stations" in permissions or (
        "manage_station" in permissions and has_access
    ):
        LOG.info(
            "Setting questionnaire score of %s on %s to %s (" "by user: %s)",
            team_name,
            station_name,
            score,
            username,
        )
        try:
            old_score, new_score = await core.set_questionnaire_score(
                session,
                team_name,
                station_name,
                score,
            )
        except NoQuestionnaireForStation:
            LOG.error(
                "No questionnaire assigned to station %r!",
                station_name,
            )
            raise HTTPException(
                500,
                "No questionnaire assigned to station %r!" % station_name,
            )
        if old_score != new_score:
            core.add_audit_log(
                session,
                username,
                schema.AuditType.QUESTIONNAIRE_SCORE,
                "Change questionnaire score of team %r from %s to %s on station %s"
                % (team_name, old_score, score, station_name),
            )
        output = {
            "new_score": new_score,
        }
        pusher.send_team_event(
            "questionnaire-score-change",
            {
                "stationName": station_name,
                "teamName": team_name,
                "score": new_score,
            },
        )
        return output
    raise AccessDenied(
        "Access denied to this station!", reason=AuthDeniedReason.ACCESS_DENIED
    )


ACTION_MAP = {
    "advance": _action_advance,
    "set_score": _action_set_score,
    "set_questionnaire_score": _action_set_questionnaire_score,
}


@ROUTER.post("")
async def create_new_job(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pusher: Annotated[PusherWrapper, Depends(get_pusher)],
    job: schema.JobSchema = Body(),
) -> JSONResponse:
    auth_user.require_permission("manage_station")
    action = job.action
    func = ACTION_MAP.get(action, None)
    if not func:
        LOG.debug("Unknown job %r requested!", job.action)
        return JSONResponse("%r is an unknown job action" % action, 400)
    else:
        LOG.debug("Matched job %r to %r", job.action, func)
    result = await func(
        session, auth_user.name, auth_user.permissions, pusher, args=job.args
    )
    return JSONResponse(result)
