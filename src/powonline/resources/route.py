import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema
from powonline.auth import User, get_user
from powonline.dependencies import get_db

ROUTER = APIRouter(prefix="/route", tags=["route"])
LOG = logging.getLogger(__name__)


@ROUTER.get("")
async def get(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schema.ListResult[schema.RouteSchema]:
    items = await core.Route.all(session)
    items = [schema.RouteSchema.model_validate(item) for item in items]
    return schema.ListResult(items=items)


@ROUTER.post("", status_code=201)
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


@ROUTER.post("/{route_name}/teams")
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
        return Response(None, 204)
    else:
        return JSONResponse("Team is already assigned to a route", 400)


@ROUTER.delete("/{route_name}/teams/{team_name}")
async def unassign_team_from_route(
    auth_user: Annotated[User, Depends(get_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    route_name: str,
    team_name: str,
):
    auth_user.require_permission("admin_routes")
    success = await core.Route.unassign_team(session, route_name, team_name)
    if success:
        return Response(None, 204)
    else:
        return JSONResponse("Unexpected error!", 500)


@ROUTER.post("/{route_name}/stations")
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
    success = await core.Route.assign_station(session, route_name, station.name)
    if success:
        return Response(None, 204)
    else:
        return JSONResponse("Unexpected error!", 500)


@ROUTER.delete("/{route_name}/stations/{station_name}")
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
        return Response(None, 204)
    else:
        return JSONResponse("Unexpected error!", 500)


@ROUTER.put("/{route_name}/color")
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


@ROUTER.put("")
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
