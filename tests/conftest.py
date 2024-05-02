import logging
import os
from pathlib import Path
from textwrap import dedent

import alembic.config
from config_resolver.core import get_config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest import fixture
from sqlalchemy import text

from powonline.dependencies import async_session
from powonline.main import create_app

LOG = logging.getLogger(__name__)


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
        yield
        try:
            alembic.config.main(argv=["--raiseerr", "downgrade", "base"])
        except:
            print("Unable to downgrade database")
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
    app = create_app()
    return app


@fixture
def test_client(app: FastAPI) -> AsyncClient:
    client = AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    )
    return client


@fixture
async def dbsession():
    session = async_session()
    with open(here("seed_cleanup.sql")) as seed:
        await session.execute(text(seed.read()))
        await session.commit()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@fixture
async def seed(dbsession):
    with open(here("seed.sql")) as seed:
        await dbsession.execute(text(seed.read()))
        await dbsession.commit()
