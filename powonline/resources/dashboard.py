from typing import Annotated

from fastapi import APIRouter, Depends
from powonline.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema

ROUTER = APIRouter(prefix="", tags=["dashboard"])


@ROUTER.get("/station/{station_name}/dashboard")
@ROUTER.get("/station/{station_name}/{relation}/dashboard")
async def for_station(
    session: Annotated[AsyncSession, Depends(get_db)],
    station_name: str,
    relation: schema.StationRelation = schema.StationRelation.UNKNOWN,
) -> list[schema.DashboardRow]:
    if relation != schema.StationRelation.UNKNOWN:
        station_name = await core.Station.related(
            session, station_name, relation
        )
        if not station_name:
            return []

    output: list[schema.DashboardRow] = []
    async for team_name, state, score, updated in core.Station.team_states(
        session, station_name
    ):
        output.append(
            schema.DashboardRow(
                team=team_name,
                state=state,
                score=score or 0,
                updated=updated,
            )
        )
    return output


@ROUTER.get("/dashboard")
async def get(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> list[schema.GlobalDashboardRow]:
    output = await core.global_dashboard(session)
    return output
