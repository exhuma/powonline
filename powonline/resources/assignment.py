from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/assignment", tags=["assignment"])


@ROUTER.get("")
async def get(session: Annotated[AsyncSession, Depends(get_db)]):
    data = await core.get_assignments(session)

    out_stations = {}
    for route_name, stations in data["stations"].items():
        out_stations[route_name] = [
            schema.StationSchema.model_validate(station) for station in stations
        ]

    out_teams = {}
    for route_name, teams in data["teams"].items():
        out_teams[route_name] = [
            schema.TeamSchema.model_validate(team) for team in teams
        ]

    return schema.AssignmentMap(teams=out_teams, stations=out_stations)
