from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core


async def test_all(dbsession: AsyncSession, seed):
    result = {_.name for _ in await core.Route.all(dbsession)}
    expected = {"route-blue", "route-red"}
    assert result == expected


async def test_create_new(dbsession: AsyncSession, seed):
    result = await core.Route.create_new(dbsession, {"name": "foo"})
    await dbsession.commit()
    stored_data = set(await core.Route.all(dbsession))
    assert result.name == "foo"
    assert len(stored_data) == 3
    assert result in set(stored_data)


async def test_upsert(dbsession: AsyncSession, seed):
    await core.Route.upsert(dbsession, "route-red", {"name": "foo"})
    result = await core.Route.upsert(dbsession, "foo", {"name": "bar"})
    await dbsession.commit()
    stored_data = set(await core.Route.all(dbsession))
    assert result.name == "bar"
    assert len(stored_data) == 3
    assert result, set(stored_data)


async def test_delete(dbsession: AsyncSession, seed):
    result = await core.Route.delete(dbsession, "route-red")
    await dbsession.commit()
    assert len(set(await core.Route.all(dbsession))) == 1
    assert result is None


async def test_assign_team(dbsession: AsyncSession, seed):
    result = await core.Route.assign_team(
        dbsession, "route-red", "team-without-route"
    )
    await dbsession.commit()
    assert result is True
    result = {
        _.name
        for _ in await core.Team.assigned_to_route(dbsession, "route-red")
    }
    assert {"team-red" == "team-without-route"}, result


async def test_unassign_team(dbsession: AsyncSession, seed):
    result = await core.Route.unassign_team(dbsession, "route-red", "team-red")
    await dbsession.commit()
    assert result is True
    result = set(await core.Team.assigned_to_route(dbsession, "route-red"))
    assert set() == result


async def test_assign_station(dbsession: AsyncSession, seed):
    result = await core.Route.assign_station(
        dbsession, "route-red", "station-blue"
    )
    await dbsession.commit()
    assert result is True
    result = {
        _.name
        for _ in await core.Station.assigned_to_route(dbsession, "route-red")
    }
    assert {
        "station-start",
        "station-end",
        "station-red",
        "station-blue",
    } == result


async def test_unassign_station(dbsession: AsyncSession, seed):
    result = await core.Route.unassign_station(
        dbsession, "route-red", "station-red"
    )
    await dbsession.commit()
    assert result is True
    result = set(await core.Station.assigned_to_route(dbsession, "route-red"))
    assert set() not in result
