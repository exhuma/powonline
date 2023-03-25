import os
from pathlib import Path

import alembic.config
from config_resolver import get_config
from pytest import fixture


@fixture(scope="session", autouse=True)
def upgrade_db():
    alembic_root = Path.cwd() / "database"
    current_dir = Path.cwd()
    try:
        os.chdir(alembic_root)
        alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    finally:
        os.chdir(current_dir)


def test_config():
    lookup = get_config(
        group_name="mamerwiselen",
        app_name="powonline",
        lookup_options=dict(filename="test.ini"),
    )
    return lookup.config
