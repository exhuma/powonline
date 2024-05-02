import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, get_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/route", tags=["route"])
LOG = logging.getLogger(__name__)


@ROUTER.get("")
async def get(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[schema.RouteSchema]:
    items = await core.Route.all(session)
    items = [schema.RouteSchema.model_validate(item) for item in items]
    return items


@ROUTER.post("")
async def post(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route: schema.RouteSchema = Body(),
):
    auth_user.require_permission("admin_routes")
    output = await core.Route.create_new(session, route.model_dump())
    return schema.RouteSchema.model_validate(output)


@ROUTER.put("/{name}")
async def put(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    route: schema.RouteSchema = Body(),
) -> schema.RouteSchema:
    auth_user.require_permission("admin_routes")
    output = await core.Route.upsert(session, name, route.model_dump())
    return schema.RouteSchema.model_validate(output)


@ROUTER.delete("/{name}")
async def delete(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str,
) -> Response:
    auth_user.require_permission("admin_routes")
    await core.Route.delete(session, name)
    return Response(None, 204)


@ROUTER.get("/user/{user_name}/stations")
async def query_station_by_user(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_name: str,
) -> list[tuple[str, bool]]:
    auth_user.require_permission("manage_permissions")
    user = await core.User.get(session, user_name)
    if not user:
        return Response("User not found", 404)
    all_stations = await core.Station.all(session)
    user_stations = await user.awaitable_attrs.stations
    user_stations = {station.name for station in user_stations or []}
    output = []
    for station in all_stations:
        output.append((station.name, station.name in user_stations))
    return output


async def assign_user_to_station(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    station_name: str,
    user: schema.UserSchema,
):
    """
    Assigns a user to a station
    """
    auth_user.require_permission("manage_permissions")
    success = await core.Station.assign_user(session, station_name, user.name)
    if success:
        return Response("", 204)
    else:
        return Response("Station is already assigned to that user", 400)


@ROUTER.post("/station/{station_name}/users")
async def assign_station_to_user(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    station_name: str,
    user: schema.UserSchema = Body(),
) -> Response:
    """
    Assigns a user to a station
    """
    auth_user.require_permission("manage_permissions")
    success = await core.User.assign_station(session, user.name, station_name)
    if success:
        return Response("", 204)
    else:
        return Response("Station is already assigned to that user", 400)


@ROUTER.post("/route/{route_name}/teams")
async def assign_team_to_route(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route_name: str,
    team: schema.TeamSchema = Body(),
):
    """
    Assign a team to a route
    """
    auth_user.require_permission("admin_routes")
    success = await core.Route.assign_team(session, route_name, team.name)
    if success:
        return "", 204
    else:
        return "Team is already assigned to a route", 400


@ROUTER.delete("/route/{route_name}/teams/{team_name}")
async def unassign_team_from_route(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route_name: str,
    team_name: str,
):
    auth_user.require_permission("admin_routes")
    success = await core.Route.unassign_team(session, route_name, team_name)
    if success:
        return "", 204
    else:
        return "Unexpected error!", 500


@ROUTER.post("/route/{route_name}/stations")
async def assign_station_to_route(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route_name: str,
    station: schema.StationSchema = Body(),
):
    """
    Assign a station to a route
    """
    auth_user.require_permission("admin_routes")
    success = core.Route.assign_station(session, route_name, station.name)
    if success:
        return "", 204
    else:
        return "Unexpected error!", 500


@ROUTER.delete("/route/{route_name}/stations/{station_name}")
async def unassign_station_from_route(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route_name: str,
    station_name: str,
):
    auth_user.require_permission("admin_routes")
    success = await core.Route.unassign_station(
        session, route_name, station_name
    )
    if success:
        return "", 204
    else:
        return "Unexpected error!", 500


@ROUTER.put("/route/{route_name}/color")
async def set_route_color(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route_name: str,
):
    """
    Replaces the route color with a new color
    """
    auth_user.require_permission("admin_stations")
    data = request.get_json()
    new_color = data["color"]
    output = await core.Route.update_color(session, route_name, new_color)
    return jsonify({"color": new_color})


@ROUTER.put("/routeStations")
def set_route_stations(session: Annotated[AsyncSession, Depends(get_db)]):
    payload = request.json
    if payload is None:
        return jsonify({"error": "no payload"}), 400
    query = session.query(Station).filter(
        Station.name == payload["stationName"]
    )
    station = query.one_or_none()
    if not station:
        return jsonify({"error": "no such station"}), 404
    station.routes.clear()
    for routeName in payload["routeNames"]:
        query = session.query(Route).filter(Route.name == routeName)
        station.routes.add(query.one())
    return jsonify(
        {
            "stationName": payload["stationName"],
            "routeNames": payload["routeNames"],
        }
    )
