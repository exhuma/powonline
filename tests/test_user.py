from pytest import fixture

from powonline import core


@fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


def test_assign_role(dbsession):
    core.User.assign_role(dbsession, "jane", "a-role")
    result = {_.name for _ in core.User.roles(dbsession, "jane")}
    assert "a-role" in result


def test_unassign_role(dbsession):
    core.User.unassign_role(dbsession, "john", "a-role")
    result = {_.name for _ in core.User.roles(dbsession, "john")}
    assert "a-role" not in result
