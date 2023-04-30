import pytest
from pytest import fixture

from powonline import core


@fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


def test_all(dbsession):
    result = {_.name for _ in core.Station.all(dbsession)}
    expected = {
        "station-start",
        "station-red",
        "station-blue",
        "station-end",
    }
    assert result == expected


def test_create_new(dbsession):
    result = core.Station.create_new(dbsession, {"name": "foo"})
    assert result.name == "foo"
    assert len(set(core.Station.all(dbsession))) == 5
    assert result in set(core.Station.all(dbsession))


def test_upsert(dbsession):
    core.Station.upsert(
        dbsession, "station-red", {"name": "foo", "contact": "bar"}
    )
    result = core.Station.all(dbsession)
    names = {_.name for _ in result}
    assert names == {"station-end", "foo", "station-start", "station-blue"}


def test_delete(dbsession):
    result = core.Station.delete(dbsession, "station-red")
    assert len(set(core.Station.all(dbsession))) == 3
    assert result is None


def test_assign_user(dbsession):
    result = core.Station.accessible_by(dbsession, "john")
    assert result == set()
    result = core.Station.assign_user(dbsession, "station-red", "john")
    assert result is True
    result = core.Station.accessible_by(dbsession, "john")
    assert result == {"station-red"}


def test_team_states(dbsession):
    result = set(core.Station.team_states(dbsession, "station-start"))
    expected = {
        ("team-blue", core.TeamState.UNKNOWN, None),
        ("team-red", core.TeamState.FINISHED, 10),
    }
    assert result == expected


@pytest.mark.parametrize(
    "relation, expected",
    [
        (
            core.StationRelation.NEXT,
            {
                ("team-blue", core.TeamState.FINISHED, 20),
            },
        ),
        (
            core.StationRelation.PREVIOUS,
            set(),
        ),
    ],
)
def test_related_station_states(dbsession, seed, relation, expected):
    """
    Ensure that we have an easy method to request the team-states of a station
    related to a given station.
    """
    result = set(
        core.Station.related_team_states(dbsession, "station-start", relation)
    )
    from pprint import pprint

    print(relation)
    pprint(result)
    assert result == expected


@pytest.mark.parametrize(
    "relation, expected",
    [
        (core.StationRelation.NEXT, "station-blue"),
        (core.StationRelation.PREVIOUS, ""),
    ],
)
def test_get_related_station(dbsession, seed, relation, expected):
    """
    Ensure that we have an easy method to determine a station related to a given
    station.
    """
    result = core.Station.related(dbsession, "station-start", relation)
    assert result == expected
