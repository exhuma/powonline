from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core


async def test_all(dbsession: AsyncSession, seed):
    result = {_.name for _ in await core.Team.all(dbsession)}
    expected = {
        "team-blue",
        "team-red",
        "team-without-route",
    }
    assert result == expected


async def test_quickfilter_without_route(dbsession: AsyncSession, seed):
    result = list(await core.Team.quickfilter_without_route(dbsession))
    await dbsession.commit()
    assert len(result) == 1
    result = result[0].name
    expected = "team-without-route"
    assert result == expected


async def test_assigned_to_route(dbsession: AsyncSession, seed):
    result = list(await core.Team.assigned_to_route(dbsession, "route-blue"))
    await dbsession.commit()
    assert len(result) == 1
    expected = "team-blue"
    assert result[0].name == expected


async def test_create_new(dbsession: AsyncSession, seed):
    result = await core.Team.create_new(
        dbsession, {"name": "foo", "email": "foo@example.com"}
    )
    await dbsession.commit()
    assert result.name == "foo"
    assert len(set(await core.Team.all(dbsession))) == 4
    assert result in set(await core.Team.all(dbsession))


async def test_upsert(dbsession: AsyncSession, seed):
    await core.Team.upsert(
        dbsession, "team-red", {"name": "foo", "contact": "bar"}
    )
    await dbsession.commit()
    new_names = {_.name for _ in await core.Team.all(dbsession)}
    assert new_names == {"team-blue", "team-without-route", "foo"}


async def test_delete(dbsession: AsyncSession, seed):
    result = await core.Team.delete(dbsession, "team-red")
    await dbsession.commit()
    assert len(set(await core.Team.all(dbsession))) == 2
    assert result is None


async def test_get_station_data(dbsession: AsyncSession, seed):
    result1 = await core.Team.get_station_data(
        dbsession, "team-red", "station-start"
    )
    result2 = await core.Team.get_station_data(
        dbsession, "team-blue", "station-finish"
    )
    expected1 = core.TeamState.FINISHED
    expected2 = core.TeamState.UNKNOWN
    assert result1.state == expected1
    assert result2.state == expected2


async def test_advance_on_station(dbsession: AsyncSession, seed):
    new_state = await core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    await dbsession.commit()
    assert new_state == core.TeamState.UNKNOWN
    new_state = await core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    await dbsession.commit()
    assert new_state == core.TeamState.ARRIVED
    new_state = await core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    await dbsession.commit()
    assert new_state == core.TeamState.FINISHED
    new_state = await core.Team.advance_on_station(
        dbsession, "team-red", "station-start"
    )
    await dbsession.commit()
    assert new_state == core.TeamState.UNKNOWN
