import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema


async def test_all(dbsession: AsyncSession, seed):
    result = {_.name for _ in await core.Station.all(dbsession)}
    expected = {
        "station-start",
        "station-red",
        "station-blue",
        "station-end",
    }
    assert result == expected


async def test_create_new(dbsession: AsyncSession, seed):
    result = await core.Station.create_new(dbsession, {"name": "foo"})
    await dbsession.commit()
    assert result.name == "foo"
    assert len(set(await core.Station.all(dbsession))) == 5
    assert result in set(await core.Station.all(dbsession))


async def test_upsert(dbsession: AsyncSession, seed):
    await core.Station.upsert(
        dbsession, "station-red", {"name": "foo", "contact": "bar"}
    )
    await dbsession.commit()
    result = await core.Station.all(dbsession)
    names = {_.name for _ in result}
    assert names == {"station-end", "foo", "station-start", "station-blue"}


async def test_delete(dbsession: AsyncSession, seed):
    result = await core.Station.delete(dbsession, "station-red")
    await dbsession.commit()
    assert len(set(await core.Station.all(dbsession))) == 3
    assert result is None


async def test_assign_user(dbsession: AsyncSession, seed):
    result = await core.Station.accessible_by(dbsession, "john")
    await dbsession.commit()
    assert result == set()
    result = await core.Station.assign_user(dbsession, "station-red", "john")
    await dbsession.commit()
    assert result is True
    result = await core.Station.accessible_by(dbsession, "john")
    await dbsession.commit()
    assert result == {"station-red"}


async def test_team_states(dbsession: AsyncSession, seed):
    result = set()
    async for row in core.Station.team_states(dbsession, "station-start"):
        result.add(row)
    await dbsession.commit()

    testable = {tuple(row[:3]) for row in result}
    expected = {
        ("team-blue", core.TeamState.UNKNOWN, None),
        ("team-red", core.TeamState.FINISHED, 10),
    }
    assert testable == expected


@pytest.mark.parametrize(
    "relation, expected",
    [
        (
            schema.StationRelation.NEXT,
            {
                ("team-blue", core.TeamState.FINISHED, 20),
            },
        ),
        (
            schema.StationRelation.PREVIOUS,
            set(),
        ),
    ],
)
async def test_related_station_states(dbsession, seed, relation, expected):
    """
    Ensure that we have an easy method to request the team-states of a station
    related to a given station.
    """
    result = set()
    async for row in core.Station.related_team_states(
        dbsession, "station-start", relation
    ):
        result.add(row)
    await dbsession.commit()
    testable = {tuple(row[:3]) for row in result}
    assert testable == expected


@pytest.mark.parametrize(
    "relation, expected",
    [
        (schema.StationRelation.NEXT, "station-blue"),
        (schema.StationRelation.PREVIOUS, ""),
    ],
)
async def test_get_related_station(dbsession, seed, relation, expected):
    """
    Ensure that we have an easy method to determine a station related to a given
    station.
    """
    result = await core.Station.related(dbsession, "station-start", relation)
    assert result == expected
