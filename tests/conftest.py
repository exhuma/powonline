import logging
import os
from pathlib import Path
from textwrap import dedent
from tkinter import INSERT

from config_resolver.core import get_config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pytest import fixture
from sqlalchemy import text

import alembic.config
from powonline.main import create_app

LOG = logging.getLogger(__name__)


def here(localname):
    from os.path import dirname, join

    return join(dirname(__file__), localname)


@fixture(scope="session", autouse=True)
def upgrade_db():
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    yield
    try:
        alembic.config.main(argv=["--raiseerr", "downgrade", "base"])
    except:
        print("Unable to downgrade database")


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
    test_config.read_string(dedent("""\
        [security]
        jwt_secret = %s
        """ % ("testing",)))
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
    from powonline.dependencies import get_async_session_maker

    session_maker = get_async_session_maker()
    async with session_maker() as session:
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
    event_id_select = await dbsession.execute(
        text("SELECT id FROM event WHERE name='event-1'")
    )
    event_id = event_id_select.scalar()
    if event_id is None:
        event_id_query = await dbsession.execute(
            text(
                "INSERT INTO event (name, time_range) VALUES ('event-1', '[2020-01-01, 2099-12-31)') RETURNING id"
            )
        )
        event_id = event_id_query.scalar()
    with open(here("seed.sql")) as seed:
        seed_content = seed.read().format(event_id=event_id)
        await dbsession.execute(text(seed_content))
        await dbsession.commit()
    try:
        yield event_id
    finally:
        await dbsession.execute(text("DELETE FROM event WHERE name='event-1'"))
        await dbsession.commit()
