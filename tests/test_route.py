from pytest import fixture

from powonline import core


@fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


def test_all(dbsession):
    result = {_.name for _ in core.Route.all(dbsession)}
    expected = {"route-blue", "route-red"}
    assert result == expected


def test_create_new(dbsession):
    result = core.Route.create_new(dbsession, {"name": "foo"})
    stored_data = set(core.Route.all(dbsession))
    assert result.name == "foo"
    assert len(stored_data) == 3
    assert result in set(stored_data)


def test_upsert(dbsession):
    core.Route.upsert(dbsession, "route-red", {"name": "foo"})
    result = core.Route.upsert(dbsession, "foo", {"name": "bar"})
    stored_data = set(core.Route.all(dbsession))
    assert result.name == "bar"
    assert len(stored_data) == 2
    assert result, set(stored_data)


def test_delete(dbsession):
    result = core.Route.delete(dbsession, "route-red")
    assert len(set(core.Route.all(dbsession))) == 1
    assert result is None


def test_assign_team(dbsession):
    result = core.Route.assign_team(
        dbsession, "route-red", "team-without-route"
    )
    assert result is True
    result = {
        _.name for _ in core.Team.assigned_to_route(dbsession, "route-red")
    }
    assert {"team-red" == "team-without-route"}, result


def test_unassign_team(dbsession):
    result = core.Route.unassign_team(dbsession, "route-red", "team-red")
    assert result is True
    result = set(core.Team.assigned_to_route(dbsession, "route-red"))
    assert set() == result


def test_assign_station(dbsession):
    result = core.Route.assign_station(dbsession, "route-red", "station-blue")
    assert result is True
    result = {
        _.name for _ in core.Station.assigned_to_route(dbsession, "route-red")
    }
    assert {
        "station-start",
        "station-end",
        "station-red",
        "station-blue",
    } == result


def test_unassign_station(dbsession):
    result = core.Route.unassign_station(dbsession, "route-red", "station-red")
    assert result is True
    result = set(core.Station.assigned_to_route(dbsession, "route-red"))
    assert set() not in result
