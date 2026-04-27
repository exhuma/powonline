from typing import Annotated, Union

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, get_optional_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/events/{event_id}/assignments", tags=["assignment"])

_CONTACT_PERMISSIONS = {"view_team_contact", "view_event_team_contact"}


def _can_view_contact(user: User | None) -> bool:
    if user is None:
        return False
    return bool(user.permissions & _CONTACT_PERMISSIONS)


@ROUTER.get("")
async def get(
    session: Annotated[AsyncSession, Depends(get_db)],
    event_id: int,
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Union[schema.AssignmentMap, schema.AssignmentMapPublic]:
    data = await core.get_assignments(session, event_id=event_id)

    if _can_view_contact(user):
        out_stations = {
            route_name: [
                schema.StationSchema.model_validate(station)
                for station in stations
            ]
            for route_name, stations in data["stations"].items()
        }
        out_teams = {
            route_name: [
                schema.TeamSchema.model_validate(team) for team in teams
            ]
            for route_name, teams in data["teams"].items()
        }
        return schema.AssignmentMap(teams=out_teams, stations=out_stations)

    out_stations_public = {
        route_name: [
            schema.StationSchemaPublic.model_validate(station)
            for station in stations
        ]
        for route_name, stations in data["stations"].items()
    }
    out_teams_public = {
        route_name: [
            schema.TeamSchemaPublic.model_validate(team) for team in teams
        ]
        for route_name, teams in data["teams"].items()
    }
    return schema.AssignmentMapPublic(
        teams=out_teams_public, stations=out_stations_public
    )
