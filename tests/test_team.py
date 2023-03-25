from pytest import fixture

from powonline import core


@fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


def test_all(dbsession):
    result = {_.name for _ in core.Team.all(dbsession)}
    expected = {
        "team-blue",
        "team-red",
        "team-without-route",
    }
    assert result == expected


def test_quickfilter_without_route(dbsession):
    result = list(core.Team.quickfilter_without_route(dbsession))
    assert len(result) == 1
    result = result[0].name
    expected = "team-without-route"
    assert result == expected


def test_assigned_to_route(dbsession):
    result = list(core.Team.assigned_to_route(dbsession, "route-blue"))
    assert len(result) == 1
    expected = "team-blue"
    assert result[0].name == expected


def test_create_new(dbsession):
    result = core.Team.create_new(
        dbsession, {"name": "foo", "email": "foo@example.com"}
    )
    assert result.name == "foo"
    assert len(set(core.Team.all(dbsession))) == 4
    assert result in set(core.Team.all(dbsession))


def test_upsert(dbsession):
    core.Team.upsert(dbsession, "team-red", {"name": "foo", "contact": "bar"})
    new_names = {_.name for _ in core.Team.all(dbsession)}
    assert new_names == {"team-blue", "team-without-route", "foo"}


def test_delete(dbsession):
    result = core.Team.delete(dbsession, "team-red")
    assert len(set(core.Team.all(dbsession))) == 2
    assert result is None


def test_get_station_data(dbsession):
    result1 = core.Team.get_station_data(dbsession, "team-red", "station-start")
    result2 = core.Team.get_station_data(
        dbsession, "team-blue", "station-finish"
    )
    expected1 = core.TeamState.FINISHED
    expected2 = core.TeamState.UNKNOWN
    assert result1.state == expected1
    assert result2.state == expected2


def test_advance_on_station(dbsession):
    new_state = core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    assert new_state == core.TeamState.UNKNOWN
    new_state = core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    assert new_state == core.TeamState.ARRIVED
    new_state = core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    assert new_state == core.TeamState.FINISHED
    new_state = core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    assert new_state == core.TeamState.UNKNOWN
