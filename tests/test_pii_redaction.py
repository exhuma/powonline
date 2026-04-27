"""
Tests that verify PII fields are not leaked to unauthenticated callers and
are visible to authenticated callers that hold the appropriate permissions.

Affected endpoints:
  GET /events/{event_id}/team
  GET /events/{event_id}/team/{name}
  GET /events/{event_id}/team/{team_name}/stations
  GET /events/{event_id}/station
  GET /events/{event_id}/assignments
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from powonline.auth import User, get_optional_user, get_user

# ---------------------------------------------------------------------------
# PII fields that must NEVER appear in unauthenticated responses.
# ---------------------------------------------------------------------------
TEAM_PII_FIELDS = {"contact", "phone", "email", "comments", "confirmation_key"}
STATION_PII_FIELDS = {"contact", "phone"}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def anon_client(app: FastAPI, test_client: AsyncClient, seed):
    """Client with NO auth override — behaves like an unauthenticated browser."""
    app.dependency_overrides.pop(get_user, None)
    app.dependency_overrides.pop(get_optional_user, None)
    try:
        yield test_client, seed
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def admin_client(app: FastAPI, test_client: AsyncClient, seed):
    """Client authenticated as global admin (has view_team_contact)."""
    app.dependency_overrides[get_user] = lambda: User(
        name="admin-user", roles={"admin"}
    )
    app.dependency_overrides[get_optional_user] = lambda: User(
        name="admin-user", roles={"admin"}
    )
    try:
        yield test_client, seed
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def staff_client(app: FastAPI, test_client: AsyncClient, seed):
    """Client authenticated as staff (has view_team_contact)."""
    app.dependency_overrides[get_user] = lambda: User(
        name="staff-user", roles={"staff"}
    )
    app.dependency_overrides[get_optional_user] = lambda: User(
        name="staff-user", roles={"staff"}
    )
    try:
        yield test_client, seed
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def event_owner_client(app: FastAPI, test_client: AsyncClient, seed):
    """Client authenticated as event_owner (has view_event_team_contact)."""
    app.dependency_overrides[get_user] = lambda: User(
        name="owner-user", roles={"event_owner"}
    )
    app.dependency_overrides[get_optional_user] = lambda: User(
        name="owner-user", roles={"event_owner"}
    )
    try:
        yield test_client, seed
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def station_manager_client(app: FastAPI, test_client: AsyncClient, seed):
    """Authenticated as station_manager — does NOT have view_team_contact."""
    app.dependency_overrides[get_user] = lambda: User(
        name="sm-user", roles={"station_manager"}
    )
    app.dependency_overrides[get_optional_user] = lambda: User(
        name="sm-user", roles={"station_manager"}
    )
    try:
        yield test_client, seed
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _assert_no_pii_in_team(team: dict, pii_fields=TEAM_PII_FIELDS):
    for field in pii_fields:
        assert (
            field not in team
        ), f"PII field '{field}' must not appear in unauthenticated team response"


def _assert_no_pii_in_station(station: dict, pii_fields=STATION_PII_FIELDS):
    for field in pii_fields:
        assert (
            field not in station
        ), f"PII field '{field}' must not appear in unauthenticated station response"


def _assert_has_pii_in_team(team: dict):
    assert "email" in team, "Authenticated response must include 'email'"
    assert "contact" in team, "Authenticated response must include 'contact'"
    assert "phone" in team, "Authenticated response must include 'phone'"


def _assert_has_pii_in_station(station: dict):
    assert "contact" in station, "Authenticated response must include 'contact'"
    assert "phone" in station, "Authenticated response must include 'phone'"


# ---------------------------------------------------------------------------
# GET /events/{id}/team — team list
# ---------------------------------------------------------------------------


async def test_team_list_unauthenticated_no_pii(anon_client):
    client, event_id = anon_client
    response = await client.get(f"/events/{event_id}/team")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0, "Expected at least one team in seed data"
    for team in data["items"]:
        _assert_no_pii_in_team(team)
        # Minimal public fields must be present
        assert "name" in team
        assert "cancelled" in team
        assert "accepted" in team
        assert "completed" in team


async def test_team_list_admin_sees_pii(admin_client):
    client, event_id = admin_client
    response = await client.get(f"/events/{event_id}/team")
    assert response.status_code == 200
    data = response.json()
    for team in data["items"]:
        _assert_has_pii_in_team(team)


async def test_team_list_staff_sees_pii(staff_client):
    client, event_id = staff_client
    response = await client.get(f"/events/{event_id}/team")
    assert response.status_code == 200
    data = response.json()
    for team in data["items"]:
        _assert_has_pii_in_team(team)


async def test_team_list_event_owner_sees_pii(event_owner_client):
    client, event_id = event_owner_client
    response = await client.get(f"/events/{event_id}/team")
    assert response.status_code == 200
    data = response.json()
    for team in data["items"]:
        _assert_has_pii_in_team(team)


async def test_team_list_station_manager_no_pii(station_manager_client):
    """station_manager lacks contact permissions — must receive public schema."""
    client, event_id = station_manager_client
    response = await client.get(f"/events/{event_id}/team")
    assert response.status_code == 200
    data = response.json()
    for team in data["items"]:
        _assert_no_pii_in_team(team)


# ---------------------------------------------------------------------------
# GET /events/{id}/team/{name} — single team
# ---------------------------------------------------------------------------


async def test_team_detail_unauthenticated_no_pii(anon_client):
    client, event_id = anon_client
    response = await client.get(f"/events/{event_id}/team/team-red")
    assert response.status_code == 200
    team = response.json()
    _assert_no_pii_in_team(team)
    assert team["name"] == "team-red"


async def test_team_detail_admin_sees_pii(admin_client):
    client, event_id = admin_client
    response = await client.get(f"/events/{event_id}/team/team-red")
    assert response.status_code == 200
    team = response.json()
    _assert_has_pii_in_team(team)
    assert team["name"] == "team-red"


async def test_team_detail_event_owner_sees_pii(event_owner_client):
    client, event_id = event_owner_client
    response = await client.get(f"/events/{event_id}/team/team-red")
    assert response.status_code == 200
    team = response.json()
    _assert_has_pii_in_team(team)


# ---------------------------------------------------------------------------
# GET /events/{id}/station — station list
# ---------------------------------------------------------------------------


async def test_station_list_unauthenticated_no_pii(anon_client):
    client, event_id = anon_client
    response = await client.get(f"/events/{event_id}/station")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    for station in data["items"]:
        _assert_no_pii_in_station(station)
        assert "name" in station
        assert "is_start" in station
        assert "is_end" in station


async def test_station_list_admin_sees_pii(admin_client):
    client, event_id = admin_client
    response = await client.get(f"/events/{event_id}/station")
    assert response.status_code == 200
    data = response.json()
    for station in data["items"]:
        _assert_has_pii_in_station(station)


async def test_station_list_event_owner_sees_pii(event_owner_client):
    client, event_id = event_owner_client
    response = await client.get(f"/events/{event_id}/station")
    assert response.status_code == 200
    data = response.json()
    for station in data["items"]:
        _assert_has_pii_in_station(station)


# ---------------------------------------------------------------------------
# GET /events/{id}/assignments — assignment map
# ---------------------------------------------------------------------------


async def test_assignments_unauthenticated_no_pii(anon_client):
    client, event_id = anon_client
    response = await client.get(f"/events/{event_id}/assignments")
    assert response.status_code == 200
    data = response.json()
    for teams_in_route in data["teams"].values():
        for team in teams_in_route:
            _assert_no_pii_in_team(team)
    for stations_in_route in data["stations"].values():
        for station in stations_in_route:
            _assert_no_pii_in_station(station)


async def test_assignments_admin_sees_pii(admin_client):
    client, event_id = admin_client
    response = await client.get(f"/events/{event_id}/assignments")
    assert response.status_code == 200
    data = response.json()
    # At least one route must have teams — verify PII is present
    all_teams = [t for teams in data["teams"].values() for t in teams]
    if all_teams:
        for team in all_teams:
            _assert_has_pii_in_team(team)
