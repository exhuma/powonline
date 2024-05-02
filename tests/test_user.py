from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core


async def test_assign_role(dbsession: AsyncSession, seed):
    await core.User.assign_role(dbsession, "jane", "a-role")
    await dbsession.commit()
    result = {_.name for _ in await core.User.roles(dbsession, "jane")}
    assert "a-role" in result


async def test_unassign_role(dbsession: AsyncSession, seed):
    await core.User.unassign_role(dbsession, "john", "a-role")
    await dbsession.commit()
    result = {_.name for _ in await core.User.roles(dbsession, "john")}
    assert "a-role" not in result
