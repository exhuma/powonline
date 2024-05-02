import json
import logging
from configparser import ConfigParser
from textwrap import dedent
from unittest import TestCase
from unittest.mock import patch

import pytest
from config_resolver.core import get_config
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from util import (
    make_dummy_route_dict,
    make_dummy_station_dict,
    make_dummy_team_dict,
)

from powonline import schema
from powonline.auth import User, get_user

LOG = logging.getLogger(__name__)


def here(localname):
    from os.path import dirname, join

    return join(dirname(__file__), localname)


TEST_HELPER = TestCase()


@pytest.fixture
async def seed(dbsession: AsyncSession, app: FastAPI, test_client: AsyncClient):
    test_config = ConfigParser()
    test_config.read_string(
        dedent(
            """\
            [security]
            jwt_secret = testing
            """
        )
    )
    app.dependency_overrides[get_config] = lambda: test_config
    try:
        with open(here("seed_cleanup.sql")) as seed:
            await dbsession.execute(text(seed.read()))
        with open(here("seed.sql")) as seed:
            await dbsession.execute(text(seed.read()))
        await dbsession.commit()
    except Exception:
        LOG.exception("Unable to execute cleanup seed")
        await dbsession.rollback()
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def red_client(app: FastAPI, test_client: AsyncClient, seed):
    app.dependency_overrides[get_user] = lambda: User(
        name="user-red", roles={"admin"}
    )
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_user, None)


# XXX async def test_fetch_list_of_teams_all(
# XXX     dbsession: AsyncSession, red_client: AsyncClient
# XXX ):
# XXX     result = await red_client.get("/team")
# XXX     print(result.content)
# XXX     1 / 0
# XXX
# XXX
# XXX async def test_fetch_list_of_teams_by_route(
# XXX     dbsession: AsyncSession, red_client: AsyncClient
# XXX ):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Team.assigned_to_route.return_value = []
# XXX         await red_client.get("/team?assigned_route=foo")
# XXX         _core.Team.assigned_to_route.assert_called_with(dbsession, "foo")
# XXX
# XXX
# XXX async def test_fetch_list_of_teams_quickfilter_without_route(
# XXX     dbsession: AsyncSession, red_client
# XXX ):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Team.quickfilter_without_route.return_value = []
# XXX         await red_client.get("/team?quickfilter=without_route")
# XXX         _core.Team.quickfilter_without_route.assert_called_with(dbsession)
# XXX
# XXX
# XXX async def test_fetch_list_of_stations(
# XXX     dbsession: AsyncSession, red_client: AsyncClient
# XXX ):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.all.return_value = [
# XXX             make_dummy_station_dict(as_mock=False, name="station1"),
# XXX             make_dummy_station_dict(as_mock=False, name="station2"),
# XXX             make_dummy_station_dict(as_mock=False, name="station3"),
# XXX         ]
# XXX         response = await red_client.get("/station")
# XXX     assert response.status_code == 200, response.content
# XXX     assert response.headers["Content-Type"] == "application/json"
# XXX     data = json.loads(response.text)
# XXX     items = data["items"]
# XXX     expected = [
# XXX         make_dummy_station_dict(name="station1"),
# XXX         make_dummy_station_dict(name="station2"),
# XXX         make_dummy_station_dict(name="station3"),
# XXX     ]
# XXX     assert items == expected
# XXX
# XXX
# XXX async def test_fetch_list_of_routes(
# XXX     dbsession: AsyncSession, red_client: AsyncClient
# XXX ):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Route.all.return_value = [
# XXX             make_dummy_route_dict(as_mock=False, name="route1"),
# XXX             make_dummy_route_dict(as_mock=False, name="route2"),
# XXX             make_dummy_route_dict(as_mock=False, name="route3"),
# XXX         ]
# XXX         response = await red_client.get("/route")
# XXX     assert response.status_code == 200, response.content
# XXX     assert response.headers["Content-Type"] == "application/json"
# XXX     data = json.loads(response.text)
# XXX     items = data["items"]
# XXX     expected = [
# XXX         make_dummy_route_dict(name="route1"),
# XXX         make_dummy_route_dict(name="route2"),
# XXX         make_dummy_route_dict(name="route3"),
# XXX     ]
# XXX     TEST_HELPER.assertCountEqual(items, expected)


async def test_update_team(dbsession: AsyncSession, red_client: AsyncClient):
    replacement_team = make_dummy_team_dict(name="foo", contact="new-contact")

    response = await red_client.put(
        "/team/old-team",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_team),
    )
    assert response.status_code == 200, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    expected = make_dummy_team_dict(name="foo", contact="new-contact")
    expected.pop("inserted")
    expected.pop("updated")
    inserted = data.pop("inserted", None)
    updated = data.pop("updated", None)
    assert inserted is not None
    assert updated is not None
    assert data == expected


async def test_update_own_station(
    dbsession: AsyncSession, red_client: AsyncClient
):
    replacement_station = make_dummy_station_dict(
        name="foo", contact="new-contact"
    )

    response = await red_client.put(
        "/station/station-red",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_station),
    )
    assert response.status_code == 200, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    expected = make_dummy_station_dict(name="foo", contact="new-contact")
    assert data == expected


async def test_update_other_station(
    dbsession: AsyncSession, red_client: AsyncClient
):
    replacement_station = make_dummy_station_dict(
        name="foo", contact="new-contact"
    )

    response = await red_client.put(
        "/station/station-blue",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_station),
    )
    assert response.status_code == 200, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    expected = make_dummy_station_dict(name="foo", contact="new-contact")
    assert data == expected


# XXX async def test_update_route(dbsession: AsyncSession, red_client: AsyncClient):
# XXX     replacement_route = make_dummy_route_dict(name="foo", contact="new-contact")
# XXX
# XXX     with patch("powonline.resources.core") as _core:
# XXX         mocked_route = make_dummy_route_dict(
# XXX             as_mock=True, name="foo", contact="new-contact"
# XXX         )
# XXX         _core.Route.upsert.return_value = mocked_route
# XXX         response = await red_client.put(
# XXX             "/route/old-route",
# XXX             headers={"Content-Type": "application/json"},
# XXX             content=json.dumps(replacement_route),
# XXX         )
# XXX     assert response.status_code == 200, response.content
# XXX     assert response.headers["Content-Type"] == "application/json"
# XXX     data = json.loads(response.text)
# XXX     expected = make_dummy_route_dict(name="foo")
# XXX     assert data == expected


async def test_create_team(dbsession: AsyncSession, red_client: AsyncClient):
    new_team = make_dummy_team_dict(name="foo", contact="new-contact")

    response = await red_client.post(
        "/team",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_team),
    )
    assert response.status_code == 201, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    expected = make_dummy_team_dict(name="foo", contact="new-contact")
    expected.pop("inserted")
    data.pop("inserted")
    assert data == expected


async def test_create_station(dbsession: AsyncSession, red_client: AsyncClient):
    new_station = make_dummy_station_dict(name="foo", contact="new-contact")

    response = await red_client.post(
        "/station",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_station),
    )
    assert response.status_code == 201, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    expected = make_dummy_station_dict(name="foo", contact="new-contact")
    assert data == expected


async def test_create_route(dbsession: AsyncSession, red_client: AsyncClient):
    new_route = make_dummy_route_dict(name="foo", contact="new-contact")

    response = await red_client.post(
        "/route",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_route),
    )
    assert response.status_code == 201, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    expected = make_dummy_route_dict(name="foo")
    assert data == expected


async def test_delete_team(dbsession: AsyncSession, red_client: AsyncClient):
    response = await red_client.delete("/team/example-team")
    assert response.status_code == 204, response.content


async def test_delete_station(dbsession: AsyncSession, red_client: AsyncClient):
    response = await red_client.delete("/station/example-station")
    assert response.status_code == 204, response.content


async def test_delete_route(dbsession: AsyncSession, red_client: AsyncClient):
    response = await red_client.delete("/route/example-route")
    assert response.status_code == 204, response.content


async def test_assign_user_to_station(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simpleuser = {"name": "john"}
    response = await red_client.post(
        "/station/station-red/users",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleuser),
    )
    assert response.status_code == 204, response.content


async def test_assign_user_to_two_stations(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simpleuser = {"name": "john"}
    response = await red_client.post(
        "/station/station-red/users",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleuser),
    )
    assert response.status_code == 204, response.content
    response = await red_client.post(
        "/station/station-blue/users",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleuser),
    )
    assert response.status_code == 204, response.content


async def test_unassign_user_from_station(
    dbsession: AsyncSession, red_client: AsyncClient
):
    response = await red_client.delete("/station/station-red/users/user-red")
    assert response.status_code == 204, response.content


async def test_assign_team_to_route(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simpleteam = {"name": "team-without-route"}
    response = await red_client.post(
        "/route/route-red/teams",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleteam),
    )
    assert response.status_code == 204, response.content


async def test_assign_team_to_two_routes(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simpleteam = {"name": "team-without-route"}
    response = await red_client.post(
        "/route/route-red/teams",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleteam),
    )
    assert response.status_code == 204, response.content
    response = await red_client.post(
        "/route/route-blue/teams",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleteam),
    )
    assert response.status_code == 400, response.content


async def test_unassign_team_from_route(
    dbsession: AsyncSession, red_client: AsyncClient
):
    response = await red_client.delete("/route/route-red/teams/team-red")
    assert response.status_code == 204, response.content


async def test_assign_role_to_user(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simplerole = {"name": "a-role"}
    response = await red_client.post(
        "/user/jane/roles",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplerole),
    )
    assert response.status_code == 204, response.content


async def test_unassign_role_from_user(
    dbsession: AsyncSession, red_client: AsyncClient
):
    response = await red_client.delete("/user/john/roles/a-role")
    assert response.status_code == 204, response.content


async def test_assign_station_to_route(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simplestation = {"name": "station-red"}
    response = await red_client.post(
        "/route/route-red/stations",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplestation),
    )
    assert response.status_code == 204, response.content


async def test_assign_station_to_two_routes(
    dbsession: AsyncSession, red_client: AsyncClient
):
    # should *pass*. A station can be on multiple routes!
    simplestation = {"name": "station-start"}
    response = await red_client.post(
        "/route/route-red/stations",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplestation),
    )
    assert response.status_code == 204, response.content
    response = await red_client.post(
        "/route/route-blue/stations",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplestation),
    )
    assert response.status_code == 204, response.content


async def test_unassign_station_from_route(
    dbsession: AsyncSession, red_client: AsyncClient
):
    response = await red_client.delete("/route/route-red/stations/station-red")
    assert response.status_code == 204, response.content


async def test_show_team_station_state(
    dbsession: AsyncSession, red_client: AsyncClient
):
    response = await red_client.get("/team/team-red/stations/station-start")
    assert response.status_code == 200, response.content
    assert response.headers["Content-Type"] == "application/json"
    data = json.loads(response.text)
    assert data["state"] == "finished"


async def test_show_team_station_state_inverse(
    dbsession: AsyncSession, red_client: AsyncClient
):
    """
    Team and Station should be interchangeable in the URL
    """
    response_a = await red_client.get("/station/station-start/teams/team-red")
    response_b = await red_client.get("/team/team-red/stations/station-start")
    assert response_a.status_code == response_b.status_code
    assert response_a.content == response_b.content


async def test_advance_team_state_auto_start(
    dbsession: AsyncSession, red_client: AsyncClient
):
    """
    Advancing on a station flagged as "start" station should set the
    "effective start time" when the new state is "finished". This means the
    team left the start station and have effectively begun the route.
    """
    job = {
        "action": "advance",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
        },
    }
    headers = {"Content-Type": "application/json"}

    # advance 6 times (cycles at least twice over the trigger state). We
    # expect the call to happen only once though!
    with patch("powonline.core.func") as _func:
        _func.now.return_value = "2018-01-01 01:02:03"
        for _ in range(6):
            await red_client.post(
                "/job", headers=headers, content=json.dumps(job)
            )
        _func.now.assert_called_once()

    state_response = await red_client.get(
        "/station/station-start/teams/team-red"
    )
    state = json.loads(state_response.text)
    assert state["state"] == "finished"
    detail_response = await red_client.get("/team/team-red")
    details = json.loads(detail_response.text)
    assert details["effective_start_time"] == "2018-01-01T01:02:03"
    assert details["finish_time"] is None


async def test_advance_team_state_auto_finish(
    dbsession: AsyncSession, red_client: AsyncClient
):
    """
    Advancing on a station flagged as "end" station should set the
    "finish time" when the new state is "finished". This means the
    team arrived at the end station and have handed in their questionnaire.
    """
    job = {
        "action": "advance",
        "args": {
            "station_name": "station-end",
            "team_name": "team-red",
        },
    }
    headers = {"Content-Type": "application/json"}

    # advance 6 times (cycles at least twice over the trigger state). We
    # expect the call to happen only once though!
    with patch("powonline.core.func") as _func:
        _func.now.return_value = "2018-02-03 01:02:03"
        for _ in range(6):
            await red_client.post(
                "/job", headers=headers, content=json.dumps(job)
            )
        _func.now.assert_called_once()

    state_response = await red_client.get("/station/station-end/teams/team-red")
    state = json.loads(state_response.text)
    assert state["state"] == "arrived"
    detail_response = await red_client.get("/team/team-red")
    details = json.loads(detail_response.text)
    assert details["effective_start_time"] is None
    assert details["finish_time"] == "2018-02-03T01:02:03"


async def test_advance_team_state(
    dbsession: AsyncSession, red_client: AsyncClient
):
    simplejob = {
        "action": "advance",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
        },
    }
    response = await red_client.post(
        "/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplejob),
    )
    assert response.status_code == 200, response.content
    data = json.loads(response.text)
    result = data["result"]
    assert result == {"state": "unknown"}


# XXX async def test_scoreboard(dbsession: AsyncSession, red_client: AsyncClient):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.scoreboard.return_value = [
# XXX             ("team1", 40),
# XXX             ("team2", 20),
# XXX             ("team3", 0),
# XXX         ]
# XXX         response = await red_client.get("/scoreboard")
# XXX         data = json.loads(response.text)
# XXX         expected = [
# XXX             ["team1", 40],
# XXX             ["team2", 20],
# XXX             ["team3", 0],
# XXX         ]
# XXX         assert data == expected


# XXX async def test_questionnaire_scores(
# XXX     dbsession: AsyncSession, red_client: AsyncClient
# XXX ):
# XXX     with patch("powonline.rootbp.questionnaire_scores") as _qs:
# XXX         _qs.return_value = {
# XXX             "team1": {"station1": {"name": "quest1", "score": 19}}
# XXX         }
# XXX         response = await red_client.get("/questionnaire-scores")
# XXX         data = json.loads(response.text)
# XXX         expected = {"team1": {"station1": {"name": "quest1", "score": 19}}}
# XXX         assert data == expected


# XXX async def test_dashboard(dbsession: AsyncSession, red_client: AsyncClient):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.team_states.return_value = [
# XXX             ("team1", core.TeamState.ARRIVED, 10, datetime(2020, 1, 1)),
# XXX             ("team2", core.TeamState.UNKNOWN, None, None),
# XXX         ]
# XXX         response = await red_client.get("/station/station-1/dashboard")
# XXX         data = json.loads(response.text)
# XXX         testable = {(row["score"], row["team"], row["state"]) for row in data}
# XXX         expected = {
# XXX             (10, "team1", "arrived"),
# XXX             (None, "team2", "unknown"),
# XXX         }
# XXX         assert testable == expected


# XXX async def test_global_dashboard(
# XXX     dbsession: AsyncSession, red_client: AsyncClient
# XXX ):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.global_dashboard.return_value = [
# XXX             {
# XXX                 "team": "team-red",
# XXX                 "stations": [
# XXX                     {
# XXX                         "name": "station-start",
# XXX                         "score": 10,
# XXX                         "state": "finished",
# XXX                     },
# XXX                     {
# XXX                         "name": "station-2",
# XXX                         "score": None,
# XXX                         "state": "unknown",
# XXX                     },
# XXX                 ],
# XXX             },
# XXX             {
# XXX                 "team": "team-2",
# XXX                 "stations": [
# XXX                     {
# XXX                         "name": "station-start",
# XXX                         "score": None,
# XXX                         "state": "unknown",
# XXX                     },
# XXX                     {
# XXX                         "name": "station-2",
# XXX                         "score": None,
# XXX                         "state": "unknown",
# XXX                     },
# XXX                 ],
# XXX             },
# XXX         ]
# XXX         response = await red_client.get("/dashboard")
# XXX         data = json.loads(response.text)
# XXX
# XXX         expected = [
# XXX             {
# XXX                 "team": "team-red",
# XXX                 "stations": [
# XXX                     {
# XXX                         "name": "station-start",
# XXX                         "score": 10,
# XXX                         "state": "finished",
# XXX                     },
# XXX                     {
# XXX                         "name": "station-2",
# XXX                         "score": None,
# XXX                         "state": "unknown",
# XXX                     },
# XXX                 ],
# XXX             },
# XXX             {
# XXX                 "team": "team-2",
# XXX                 "stations": [
# XXX                     {
# XXX                         "name": "station-start",
# XXX                         "score": None,
# XXX                         "state": "unknown",
# XXX                     },
# XXX                     {
# XXX                         "name": "station-2",
# XXX                         "score": None,
# XXX                         "state": "unknown",
# XXX                     },
# XXX                 ],
# XXX             },
# XXX         ]
# XXX         assert data == expected


@pytest.fixture
def usm_client(app: FastAPI, test_client: AsyncClient, seed):
    """
    A client with a "user-station manager" authenticated
    """
    app.dependency_overrides[get_user] = lambda: User(
        name="user-station-manager", roles={"station_manager"}
    )
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_user)


# XXX async def test_usm_fetch_list_of_teams(usm_client):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Team.all.return_value = []
# XXX         response = await usm_client.get("/team")
# XXX         assert response.status_code < 400


# XXX async def test_usm_fetch_list_of_stations(usm_client):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.all.return_value = []
# XXX         response = await usm_client.get("/station")
# XXX     assert response.status_code < 400
# XXX
# XXX
# XXX async def test_usm_fetch_list_of_routes(usm_client):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Route.all.return_value = []
# XXX         response = await usm_client.get("/route")
# XXX         assert response.status_code < 400


async def test_usm_update_team(usm_client):
    replacement_team = make_dummy_team_dict(name="foo", contact="new-contact")

    response = await usm_client.put(
        "/team/old-team",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_team),
    )
    # should fail: access denied
    assert response.status_code == 403, response.content


async def test_usm_update_own_station(usm_client):
    replacement_station = make_dummy_station_dict(
        name="foo", contact="new-contact"
    )

    response = await usm_client.put(
        "/station/station-red",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_station),
    )
    assert response.status_code < 400, response.content


async def test_usm_update_other_station(usm_client):
    # should fail: access denied
    replacement_station = make_dummy_station_dict(
        name="foo", contact="new-contact"
    )

    response = await usm_client.put(
        "/station/station-blue",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_station),
    )
    assert response.status_code == 403, response.content


# XXX async def test_usm_update_route(usm_client):
# XXX     # should fail: access denied
# XXX     replacement_route = make_dummy_route_dict(name="foo", contact="new-contact")
# XXX
# XXX     with patch("powonline.resources.core") as _core:
# XXX         mocked_route = make_dummy_route_dict(
# XXX             as_mock=True, name="foo", contact="new-contact"
# XXX         )
# XXX         _core.Route.upsert.return_value = mocked_route
# XXX         response = await usm_client.put(
# XXX             "/route/old-route",
# XXX             headers={"Content-Type": "application/json"},
# XXX             content=json.dumps(replacement_route),
# XXX         )
# XXX     assert response.status_code == 401, response.content


async def test_usm_create_team(usm_client):
    # should fail: access denied
    new_team = make_dummy_team_dict(name="foo", contact="new-contact")

    response = await usm_client.post(
        "/team",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_team),
    )
    assert response.status_code == 403, response.content


async def test_usm_create_station(usm_client):
    # should fail: access denied
    new_station = make_dummy_station_dict(name="foo", contact="new-contact")

    response = await usm_client.post(
        "/station",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_station),
    )
    assert response.status_code == 403, response.content


async def test_usm_create_route(usm_client):
    # should fail: access denied
    new_route = make_dummy_route_dict(name="foo", contact="new-contact")

    response = await usm_client.post(
        "/route",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_route),
    )
    assert response.status_code == 403, response.content


async def test_usm_delete_team(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/team/example-team")
    assert response.status_code == 403, response.content


async def test_usm_delete_station(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/station/example-station")
    assert response.status_code == 403, response.content


async def test_usm_delete_route(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/route/example-route")
    assert response.status_code == 403, response.content


async def test_usm_assign_user_to_station(usm_client):
    # should fail: access denied
    simpleuser = {"name": "john"}
    response = await usm_client.post(
        "/station/station-red/users",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleuser),
    )
    assert response.status_code == 403, response.content


async def test_usm_unassign_user_from_station(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/station/station-red/users/user-red")
    assert response.status_code == 403, response.content


async def test_usm_assign_team_to_route(usm_client):
    # should fail: access denied
    simpleteam = {"name": "team-without-route"}
    response = await usm_client.post(
        "/route/route-red/teams",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleteam),
    )
    assert response.status_code == 403, response.content


async def test_usm_unassign_team_from_route(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/route/route-red/teams/team-red")
    assert response.status_code == 403, response.content


async def test_usm_assign_role_to_user(usm_client):
    # should fail: access denied
    simplerole = {"name": "a-role"}
    response = await usm_client.post(
        "/user/jane/roles",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplerole),
    )
    assert response.status_code == 403, response.content


async def test_usm_unassign_role_from_user(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/user/john/roles/a-role")
    assert response.status_code == 403, response.content


async def test_usm_assign_station_to_route(usm_client):
    # should fail: access denied
    simplestation = {"name": "station-red"}
    response = await usm_client.post(
        "/route/route-red/stations",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplestation),
    )
    assert response.status_code == 403, response.content


async def test_usm_unassign_station_from_route(usm_client):
    # should fail: access denied
    response = await usm_client.delete("/route/route-red/stations/station-red")
    assert response.status_code == 403, response.content


async def test_usm_advance_team_state(usm_client):
    # should pass: user has permission for this station
    simplejob = {
        "action": "advance",
        "args": {
            "station_name": "station-red",
            "team_name": "team-red",
        },
    }
    response = await usm_client.post(
        "/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplejob),
    )
    assert response.status_code == 200, response.content
    data = json.loads(response.text)
    result = data["result"]
    assert result == {"state": "arrived"}


async def test_usm_advance_team_state_on_other_stations(usm_client):
    # should fail: access denied
    simplejob = {
        "action": "advance",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
        },
    }
    response = await usm_client.post(
        "/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplejob),
    )
    assert response.status_code == 403, response.content


# XXX async def test_anon_fetch_list_of_teams(test_client: AsyncClient):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Team.all.return_value = []
# XXX         response = await test_client.get("/team")
# XXX         assert response.status_code < 400
# XXX
# XXX
# XXX async def test_anon_fetch_list_of_stations(test_client: AsyncClient):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.all.return_value = []
# XXX         response = await test_client.get("/station")
# XXX     assert response.status_code < 400, response.content
# XXX
# XXX
# XXX async def test_anon_fetch_list_of_routes(test_client: AsyncClient):
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Route.all.return_value = []
# XXX         response = await test_client.get("/route")
# XXX     assert response.status_code < 400, response.content


async def test_anon_update_team(test_client: AsyncClient):
    # should fail: access denied
    replacement_team = make_dummy_team_dict(name="foo", contact="new-contact")

    response = await test_client.put(
        "/team/old-team",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_team),
    )
    assert response.status_code == 401, response.content


async def test_anon_update_own_station(test_client: AsyncClient):
    # should fail: access denied
    replacement_station = make_dummy_station_dict(
        name="foo", contact="new-contact"
    )

    response = await test_client.put(
        "/station/station-red",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_station),
    )
    assert response.status_code == 401, response.content


async def test_anon_update_other_station(test_client: AsyncClient):
    # should fail: access denied
    replacement_station = make_dummy_station_dict(
        name="foo", contact="new-contact"
    )

    response = await test_client.put(
        "/station/not-my-station",
        headers={"Content-Type": "application/json"},
        content=json.dumps(replacement_station),
    )
    assert response.status_code == 401, response.content


# XXX async def test_anon_update_route(test_client: AsyncClient):
# XXX     # should fail: access denied
# XXX     replacement_route = make_dummy_route_dict(name="foo", contact="new-contact")
# XXX
# XXX     with patch("powonline.resources.core") as _core:
# XXX         mocked_route = make_dummy_route_dict(
# XXX             as_mock=True, name="foo", contact="new-contact"
# XXX         )
# XXX         _core.Route.upsert.return_value = mocked_route
# XXX         response = await test_client.put(
# XXX             "/route/old-route",
# XXX             headers={"Content-Type": "application/json"},
# XXX             content=json.dumps(replacement_route),
# XXX         )
# XXX     assert response.status_code == 401, response.content


async def test_anon_create_team(test_client: AsyncClient):
    # should fail: access denied
    new_team = make_dummy_team_dict(name="foo", contact="new-contact")

    response = await test_client.post(
        "/team",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_team),
    )
    assert response.status_code == 401, response.content


async def test_anon_create_station(test_client: AsyncClient):
    # should fail: access denied
    new_station = make_dummy_station_dict(name="foo", contact="new-contact")

    response = await test_client.post(
        "/station",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_station),
    )
    assert response.status_code == 401, response.content


async def test_anon_create_route(test_client: AsyncClient):
    # should fail: access denied
    new_route = make_dummy_route_dict(name="foo", contact="new-contact")

    response = await test_client.post(
        "/route",
        headers={"Content-Type": "application/json"},
        content=json.dumps(new_route),
    )
    assert response.status_code == 401, response.content


async def test_anon_delete_team(test_client: AsyncClient):
    # should fail
    response = await test_client.delete("/team/example-team")
    assert response.status_code == 401, response.content


async def test_anon_delete_station(test_client: AsyncClient):
    # should fail: access denied
    response = await test_client.delete("/station/example-station")
    assert response.status_code == 401, response.content


async def test_anon_delete_route(test_client: AsyncClient):
    # should fail: access denied
    response = await test_client.delete("/route/example-route")
    assert response.status_code == 401, response.content


async def test_anon_assign_user_to_station(test_client: AsyncClient):
    # should fail: access denied
    simpleuser = {"name": "john"}
    response = await test_client.post(
        "/station/station-red/users",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleuser),
    )
    assert response.status_code == 401, response.content


async def test_anon_unassign_user_from_station(test_client: AsyncClient):
    # should fail: access denied
    response = await test_client.delete("/station/station-red/users/user-red")
    assert response.status_code == 401, response.content


async def test_anon_assign_team_to_route(test_client: AsyncClient):
    # should fail: access denied
    simpleteam = {"name": "team-without-route"}
    response = await test_client.post(
        "/route/route-red/teams",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simpleteam),
    )
    assert response.status_code == 401, response.content


async def test_anon_unassign_team_from_route(test_client: AsyncClient):
    # should fail: access denied
    response = await test_client.delete("/route/route-red/teams/team-red")
    assert response.status_code == 401, response.content


async def test_anon_assign_role_to_user(test_client: AsyncClient):
    # should fail: access denied
    simplerole = {"name": "a-role"}
    response = await test_client.post(
        "/user/jane/roles",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplerole),
    )
    assert response.status_code == 401, response.content


async def test_anon_unassign_role_from_user(test_client: AsyncClient):
    # should fail: access denied
    response = await test_client.delete("/user/john/roles/a-role")
    assert response.status_code == 401, response.content


async def test_anon_assign_station_to_route(test_client: AsyncClient):
    # should fail: access denied
    simplestation = {"name": "station-red"}
    response = await test_client.post(
        "/route/route-red/stations",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplestation),
    )
    assert response.status_code == 401, response.content


async def test_anon_unassign_station_from_route(test_client: AsyncClient):
    # should fail: access denied
    response = await test_client.delete("/route/route-red/stations/station-red")
    assert response.status_code == 401, response.content


async def test_anon_advance_team_state(test_client: AsyncClient):
    # should fail: access denied
    simplejob = {
        "action": "advance",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
        },
    }
    response = await test_client.post(
        "/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplejob),
    )
    assert response.status_code == 401, response.content


async def test_anon_advance_team_state_on_other_stations(
    test_client: AsyncClient,
):
    # should fail: access denied
    simplejob = {
        "action": "advance",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
        },
    }
    response = await test_client.post(
        "/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(simplejob),
    )
    assert response.status_code == 401, response.content


# XXX async def test_anon_related_states_next(
# XXX     dbsession: AsyncSession, test_client: AsyncClient
# XXX ):
# XXX     url_node = "next"  # TODO: Can be parametrised in pytest-style tests
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.team_states.return_value = [
# XXX             ("team1", core.TeamState.ARRIVED, 10, datetime(2020, 1, 1)),
# XXX             ("team2", core.TeamState.UNKNOWN, None, None),
# XXX         ]
# XXX         response = await test_client.get(
# XXX             f"/station/station-1/{url_node}/dashboard"
# XXX         )
# XXX         assert response.status_code == 200
# XXX         _core.Station.related.assert_called_with(
# XXX             dbsession, "station-1", schema.StationRelation.NEXT
# XXX         )
# XXX         data = json.loads(response.text)
# XXX         testable = {(row["score"], row["team"], row["state"]) for row in data}
# XXX         expected = {
# XXX             (10, "team1", "arrived"),
# XXX             (None, "team2", "unknown"),
# XXX         }
# XXX         assert testable == expected


# XXX async def test_anon_related_states_previous(
# XXX     dbsession: AsyncSession, test_client: AsyncClient
# XXX ):
# XXX     url_node = "previous"  # TODO: Can be parametrised in pytest-style tests
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.team_states.return_value = [
# XXX             ("team1", core.TeamState.ARRIVED, 10, datetime(2020, 1, 2)),
# XXX             ("team2", core.TeamState.UNKNOWN, None, None),
# XXX         ]
# XXX         response = await test_client.get(
# XXX             f"/station/station-1/{url_node}/dashboard"
# XXX         )
# XXX         assert response.status_code == 200
# XXX         _core.Station.related.assert_called_with(
# XXX             dbsession, "station-1", schema.StationRelation.PREVIOUS
# XXX         )
# XXX         data = json.loads(response.text)
# XXX         testable = {(row["score"], row["team"], row["state"]) for row in data}
# XXX         expected = {
# XXX             (10, "team1", "arrived"),
# XXX             (None, "team2", "unknown"),
# XXX         }
# XXX         assert testable == expected


async def test_anon_related_states_invalid_state(test_client: AsyncClient):
    """
    If a user specifies an invalid state, we want a 4xx error, not a 5xx error
    """
    response = await test_client.get(
        "/station/station-1/this-state-is-wrong/dashboard"
    )
    assert response.status_code == 422, response.content
    assert "this-state-is-wrong" in response.text


# XXX async def test_anon_related_station_next(
# XXX     dbsession: AsyncSession, test_client: AsyncClient
# XXX ):
# XXX     """
# XXX     Ensure that we can easily get the station immediately following a given
# XXX     station.
# XXX     """
# XXX     url_node = "next"  # TODO: Can be parametrised in pytest-style tests
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.related.return_value = "foobar"
# XXX         response = await test_client.get(
# XXX             f"/station/station-1/related/{url_node}"
# XXX         )
# XXX         assert response.status_code == 200, response.text
# XXX         _core.Station.related.assert_called_with(
# XXX             dbsession, "station-1", schema.StationRelation.NEXT
# XXX         )
# XXX         data = json.loads(response.text)
# XXX         assert data == "foobar"


# XXX async def test_anon_related_station_previous(
# XXX     dbsession: AsyncSession, test_client: AsyncClient
# XXX ):
# XXX     url_node = "previous"  # TODO: Can be parametrised in pytest-style tests
# XXX     with patch("powonline.resources.core") as _core:
# XXX         _core.Station.related.return_value = "foobar"
# XXX         response = await test_client.get(
# XXX             f"/station/station-1/related/{url_node}"
# XXX         )
# XXX         assert response.status_code == 200, response.text
# XXX         _core.Station.related.assert_called_with(
# XXX             dbsession, "station-1", schema.StationRelation.PREVIOUS
# XXX         )
# XXX         data = json.loads(response.text)
# XXX         assert data == "foobar"


async def test_anon_related_station_invalid_state(test_client: AsyncClient):
    """
    If a user specifies an invalid state, we want a 4xx error, not a 5xx error
    """
    response = await test_client.get(
        "/station/station-1/related/this-state-is-wrong"
    )
    assert response.status_code == 422, response.text
    assert "this-state-is-wrong" in response.text
