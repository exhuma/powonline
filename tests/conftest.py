import os
from pathlib import Path
from textwrap import dedent

import alembic.config
from config_resolver import get_config
from pytest import fixture
from sqlalchemy import text

from powonline import model
from powonline.web import make_app


def here(localname):
    from os.path import dirname, join

    return join(dirname(__file__), localname)


@fixture(scope="session", autouse=True)
def upgrade_db():
    alembic_root = Path.cwd() / "database"
    current_dir = Path.cwd()
    try:
        os.chdir(alembic_root)
        alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    finally:
        os.chdir(current_dir)


@fixture
def test_config():
    lookup = get_config(
        group_name="mamerwiselen",
        app_name="powonline",
        lookup_options=dict(filename="test.ini"),
    )
    return lookup.config


@fixture
def app(test_config):
    test_config.read_string(
        dedent(
            """\
        [security]
        jwt_secret = %s
        """
            % ("testing",)
        )
    )
    return make_app(test_config)


@fixture
def dbsession():
    try:
        yield model.DB.session
    finally:
        model.DB.session.remove()


@fixture
def seed(dbsession):
    with open(here("seed_cleanup.sql")) as seed:
        try:
            model.DB.session.execute(text(seed.read()))
            model.DB.session.commit()
        except Exception as exc:
            LOG.exception("Unable to execute cleanup seed")
            model.DB.session.rollback()
    with open(here("seed.sql")) as seed:
        model.DB.session.execute(text(seed.read()))
        model.DB.session.commit()
