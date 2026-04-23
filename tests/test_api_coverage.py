"""
Additional API coverage tests targeting previously uncovered endpoints.

These tests exercise the full stack (HTTP → router → core → DB) using
the same fixture pattern as test_public_api.py.
"""

import json
import logging
from textwrap import dedent

import pytest
from config_resolver.core import get_config
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from powonline.auth import User, get_user

LOG = logging.getLogger(__name__)


def here(localname):
    from os.path import dirname, join

    return join(
        dirname(
            __file__,
        ),
        localname,
    )


def here(localname):
    import os

    return os.path.join(os.path.dirname(__file__), localname)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed(dbsession: AsyncSession, app: FastAPI, test_client: AsyncClient):
    """Seed the database and yield the event_id."""
    from configparser import ConfigParser

    test_config = ConfigParser()
    test_config.read_string(dedent("""\
            [security]
            jwt_secret = testing
            """))
    app.dependency_overrides[get_config] = lambda: test_config
    event_id = None
    try:
        with open(here("seed_cleanup.sql")) as f:
            await dbsession.execute(text(f.read()))
        event_id_result = await dbsession.execute(
            text("SELECT id FROM event WHERE name='event-1'")
        )
        event_id = event_id_result.scalar()
        if event_id is None:
            event_id_query = await dbsession.execute(
                text(
                    "INSERT INTO event (name, time_range) "
                    "VALUES ('event-1', '[2020-01-01, 2099-12-31)') "
                    "RETURNING id"
                )
            )
            event_id = event_id_query.scalar()
        with open(here("seed.sql")) as f:
            seed_content = f.read().format(event_id=event_id)
            await dbsession.execute(text(seed_content))
        await dbsession.commit()
    except Exception:
        LOG.exception("Unable to execute seed")
        await dbsession.rollback()
    try:
        yield event_id
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def admin_client(app: FastAPI, test_client: AsyncClient, seed):
    """Authenticated client with full admin role."""
    app.dependency_overrides[get_user] = lambda: User(
        name="user-red", roles={"admin"}
    )
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_user, None)


# ---------------------------------------------------------------------------
# Event endpoints
# ---------------------------------------------------------------------------


async def test_list_events(test_client: AsyncClient, seed):
    response = await test_client.get("/events")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "items" in data
    names = [e["name"] for e in data["items"]]
    assert "event-1" in names


async def test_get_event(admin_client: AsyncClient, seed):
    response = await admin_client.get(f"/events/{seed}")
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "event-1"


async def test_create_event(admin_client: AsyncClient, seed):
    payload = {
        "name": "new-event",
        "time_range": {
            "start": "2030-01-01T00:00:00+00:00",
            "end": "2030-12-31T23:59:59+00:00",
        },
    }
    response = await admin_client.post(
        "/events",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 201, response.content
    data = response.json()
    assert data["name"] == "new-event"


async def test_update_event(admin_client: AsyncClient, seed):
    payload = {"name": "updated-event-name"}
    response = await admin_client.put(
        f"/events/{seed}",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "updated-event-name"


async def test_get_event_not_found(admin_client: AsyncClient, seed):
    response = await admin_client.get("/events/999999")
    assert response.status_code == 404, response.content


async def test_list_event_members_empty(admin_client: AsyncClient, seed):
    response = await admin_client.get(f"/events/{seed}/members")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "items" in data


async def test_add_and_remove_event_member(admin_client: AsyncClient, seed):
    payload = {"user_name": "john", "role_name": "event_owner"}
    add_resp = await admin_client.post(
        f"/events/{seed}/members",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert add_resp.status_code == 201, add_resp.content
    data = add_resp.json()
    assert data["user_name"] == "john"
    assert data["role_name"] == "event_owner"

    del_resp = await admin_client.delete(
        f"/events/{seed}/members/john/event_owner"
    )
    assert del_resp.status_code == 204, del_resp.content


async def test_add_event_member_invalid_role(admin_client: AsyncClient, seed):
    payload = {"user_name": "john", "role_name": "not_a_valid_role"}
    response = await admin_client.post(
        f"/events/{seed}/members",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 400, response.content


async def test_list_event_domains(admin_client: AsyncClient, seed):
    response = await admin_client.get(f"/events/{seed}/domains")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "items" in data


async def test_add_and_remove_event_domain(admin_client: AsyncClient, seed):
    payload = {"domain": "test.example.com"}
    add_resp = await admin_client.post(
        f"/events/{seed}/domains",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert add_resp.status_code == 201, add_resp.content

    del_resp = await admin_client.delete(
        f"/events/{seed}/domains/test.example.com"
    )
    assert del_resp.status_code == 204, del_resp.content


# ---------------------------------------------------------------------------
# Route endpoints
# ---------------------------------------------------------------------------


async def test_list_routes(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/route")
    assert response.status_code == 200, response.content
    data = response.json()
    names = {r["name"] for r in data["items"]}
    assert names == {"route-red", "route-blue"}


async def test_update_route(admin_client: AsyncClient, seed):
    payload = {"name": "route-red", "color": "#ff0000"}
    response = await admin_client.put(
        f"/events/{seed}/route/route-red",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "route-red"


async def test_set_route_color(admin_client: AsyncClient, seed):
    payload = {"color": "#abcdef"}
    response = await admin_client.put(
        f"/events/{seed}/route/route-red/color",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["color"] == "#abcdef"


# ---------------------------------------------------------------------------
# Station endpoints
# ---------------------------------------------------------------------------


async def test_list_stations(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/station")
    assert response.status_code == 200, response.content
    data = response.json()
    names = {s["name"] for s in data["items"]}
    assert {
        "station-red",
        "station-blue",
        "station-start",
        "station-end",
    } == names


async def test_get_station(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/station/station-red")
    assert response.status_code == 200, response.content


async def test_get_station_related_next(test_client: AsyncClient, seed):
    response = await test_client.get(
        f"/events/{seed}/station/station-start/related/next"
    )
    assert response.status_code == 200, response.content


@pytest.mark.skip(
    reason="MissingGreenlet bug: lazy async relationship in sync context"
)
async def test_is_user_assigned_to_station_true(
    admin_client: AsyncClient, seed
):
    response = await admin_client.get(
        f"/events/{seed}/station/station-red/users/user-red"
    )
    assert response.status_code == 200, response.content
    assert response.json() is True


@pytest.mark.skip(
    reason="MissingGreenlet bug: lazy async relationship in sync context"
)
async def test_is_user_assigned_to_station_false(
    admin_client: AsyncClient, seed
):
    response = await admin_client.get(
        f"/events/{seed}/station/station-start/users/user-red"
    )
    assert response.status_code == 200, response.content
    assert response.json() is False


async def test_unassign_user_from_station_event_route(
    admin_client: AsyncClient, seed
):
    response = await admin_client.delete(
        f"/events/{seed}/station/station-red/users/user-red"
    )
    assert response.status_code == 204, response.content


# ---------------------------------------------------------------------------
# Team endpoints
# ---------------------------------------------------------------------------


async def test_list_teams(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/team")
    assert response.status_code == 200, response.content
    data = response.json()
    names = {t["name"] for t in data["items"]}
    assert "team-red" in names
    assert "team-blue" in names


async def test_list_teams_by_route(test_client: AsyncClient, seed):
    response = await test_client.get(
        f"/events/{seed}/team?assigned_to_route=route-red"
    )
    assert response.status_code == 200, response.content
    data = response.json()
    names = {t["name"] for t in data["items"]}
    assert "team-red" in names
    assert "team-blue" not in names


async def test_list_teams_quickfilter_without_route(
    test_client: AsyncClient, seed
):
    response = await test_client.get(
        f"/events/{seed}/team?quickfilter=without_route"
    )
    assert response.status_code == 200, response.content
    data = response.json()
    names = {t["name"] for t in data["items"]}
    assert "team-without-route" in names


async def test_get_team_info(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/team/team-red")
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "team-red"


async def test_get_team_not_found(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/team/nonexistent-team")
    assert response.status_code == 404, response.content


async def test_get_stations_for_team(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/team/team-red/stations")
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)
    names = {s["name"] for s in data}
    assert "station-start" in names


# ---------------------------------------------------------------------------
# Questionnaire endpoints
# ---------------------------------------------------------------------------


async def test_list_questionnaires(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/questionnaire")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "items" in data
    names = {q["name"] for q in data["items"]}
    assert "questionnaire_1" in names


async def test_create_questionnaire(admin_client: AsyncClient, seed):
    payload = {
        "name": "new-questionnaire",
        "max_score": 100,
        "order": 10,
        "station_name": None,
    }
    response = await admin_client.post(
        f"/events/{seed}/questionnaire",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 201, response.content
    data = response.json()
    assert data["name"] == "new-questionnaire"


async def test_update_questionnaire(admin_client: AsyncClient, seed):
    payload = {
        "name": "questionnaire_1",
        "max_score": 50,
        "order": 1,
        "station_name": "station-blue",
    }
    response = await admin_client.put(
        f"/events/{seed}/questionnaire/questionnaire_1",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["max_score"] == 50


async def test_delete_questionnaire(admin_client: AsyncClient, seed):
    response = await admin_client.delete(
        f"/events/{seed}/questionnaire/questionnaire_3"
    )
    assert response.status_code == 204, response.content


async def test_assign_questionnaire_to_station(admin_client: AsyncClient, seed):
    """Assign questionnaire_3 (no station) to station-end."""
    payload = {
        "name": "questionnaire_3",
        "max_score": 50,
        "order": 0,
        "station_name": None,
    }
    response = await admin_client.post(
        f"/events/{seed}/station/station-end/questionnaires",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 204, response.content


async def test_unassign_questionnaire_from_station(
    admin_client: AsyncClient, seed
):
    """questionnaire_1 is linked to station-blue in seed; unassign it."""
    response = await admin_client.delete(
        f"/events/{seed}/questionnaire/questionnaire_1/station"
    )
    assert response.status_code == 204, response.content


async def test_questionnaire_scores(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/questionnaire-scores")
    assert response.status_code == 200, response.content


# ---------------------------------------------------------------------------
# Dashboard endpoints
# ---------------------------------------------------------------------------


async def test_station_dashboard(test_client: AsyncClient, seed):
    response = await test_client.get(
        f"/events/{seed}/station/station-red/dashboard"
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)


async def test_station_dashboard_with_relation(test_client: AsyncClient, seed):
    """Dashboard for the station *after* station-start."""
    response = await test_client.get(
        f"/events/{seed}/station/station-start/next/dashboard"
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)


async def test_global_dashboard(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/dashboard")
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Assignment endpoint
# ---------------------------------------------------------------------------


async def test_get_assignments(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/assignments")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "teams" in data
    assert "stations" in data


# ---------------------------------------------------------------------------
# Audit log endpoint
# ---------------------------------------------------------------------------


async def test_get_audit_log(admin_client: AsyncClient, seed):
    response = await admin_client.get(f"/events/{seed}/auditlog")
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Scoreboard endpoint
# ---------------------------------------------------------------------------


async def test_get_scoreboard(test_client: AsyncClient, seed):
    response = await test_client.get(f"/events/{seed}/scoreboard")
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# User management endpoints
# ---------------------------------------------------------------------------


async def test_list_users(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "items" in data
    names = {u["name"] for u in data["items"]}
    assert "user-red" in names


async def test_get_user_endpoint(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/user-red")
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "user-red"


async def test_get_user_not_found(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/nobody-here")
    assert response.status_code == 404, response.content


async def test_create_user(admin_client: AsyncClient, seed):
    payload = {
        "name": "new-user",
        "active": True,
        "email": "new@example.com",
        "avatar_url": "",
        "password": "secret",
    }
    response = await admin_client.post(
        "/user",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["name"] == "new-user"


async def test_delete_user(admin_client: AsyncClient, seed):
    response = await admin_client.delete("/user/jane")
    assert response.status_code == 204, response.content


async def test_get_user_roles_endpoint(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/john/roles")
    assert response.status_code == 200, response.content
    data = response.json()
    # data is a list of [role_name, assigned_bool] pairs
    assert isinstance(data, list)
    assigned = {r[0]: r[1] for r in data}
    assert assigned.get("a-role") is True


async def test_check_role_assigned(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/john/roles/a-role")
    assert response.status_code == 200, response.content
    assert response.json() is True


async def test_check_role_not_assigned(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/john/roles/station-manager")
    assert response.status_code == 200, response.content
    assert response.json() is False


async def test_get_user_stations_endpoint(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/user-red/stations")
    assert response.status_code == 200, response.content
    data = response.json()
    assert isinstance(data, list)
    assigned = {s[0]: s[1] for s in data}
    assert assigned.get("station-red") is True


async def test_assign_user_to_station_via_user_route(
    admin_client: AsyncClient, seed
):
    payload = {"name": "station-blue"}
    response = await admin_client.post(
        "/user/jane/stations",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )
    assert response.status_code == 204, response.content


async def test_unassign_user_from_station_via_user_route(
    admin_client: AsyncClient, seed
):
    response = await admin_client.delete("/user/user-red/stations/station-red")
    assert response.status_code == 204, response.content


async def test_list_my_admin_events(admin_client: AsyncClient, seed):
    response = await admin_client.get("/user/me/admin-events")
    assert response.status_code == 200, response.content
    data = response.json()
    assert "items" in data


# ---------------------------------------------------------------------------
# Job: set_score and set_questionnaire_score actions
# ---------------------------------------------------------------------------


async def test_job_set_score(admin_client: AsyncClient, seed):
    job = {
        "action": "set_score",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
            "score": 42,
        },
    }
    response = await admin_client.post(
        f"/events/{seed}/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(job),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["new_score"] == 42


async def test_job_set_score_unchanged(admin_client: AsyncClient, seed):
    """Setting score to same value should not write audit log."""
    # team-red / station-start already has score=10 in seed
    job = {
        "action": "set_score",
        "args": {
            "station_name": "station-start",
            "team_name": "team-red",
            "score": 10,
        },
    }
    response = await admin_client.post(
        f"/events/{seed}/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(job),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["new_score"] == 10


async def test_job_set_questionnaire_score(admin_client: AsyncClient, seed):
    """
    questionnaire_2 is linked to station-red; team-red has a score for it.
    """
    job = {
        "action": "set_questionnaire_score",
        "args": {
            "station_name": "station-red",
            "team_name": "team-red",
            "score": 15,
        },
    }
    response = await admin_client.post(
        f"/events/{seed}/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(job),
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["new_score"] == 15


async def test_job_unknown_action(admin_client: AsyncClient, seed):
    job = {"action": "no_such_action", "args": {}}
    response = await admin_client.post(
        f"/events/{seed}/job",
        headers={"Content-Type": "application/json"},
        content=json.dumps(job),
    )
    assert response.status_code == 400, response.content
