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


def test_new_social_login(dbsession):
    """
    When a user is logged in via a social login, the user is created
    """
    user = core.User.by_social_connection(
        dbsession, "github", "123456789", defaults={"email": "user@example.com"}
    )
    assert user.name == "user@example.com"
    assert user.password != ""
    assert user.password_is_plaintext is False
    assert user.oauth_connection and len(user.oauth_connection) == 1
    connection = user.oauth_connection[0]
    assert connection.provider_id == "github"
    assert connection.provider_user_id == "123456789"
