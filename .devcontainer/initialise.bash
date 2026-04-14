#!/bin/bash

# -----------------------------------------------------------------------------
#  Install any additional dependencies into the dev-container that are
#  needed/useful during development
# -----------------------------------------------------------------------------

set -xe

sudo apt-get update && sudo apt-get install -y entr

curl -LsSf https://astral.sh/uv/install.sh | sh

uv tool install fabric
uv tool install pre-commit

fab develop

uv run alembic upgrade head
uv run alembic show head

psql -v ON_ERROR_STOP=1 -X1qf \
    .devcontainer/sample-data.sql \
    postgresql://postgres:postgres@db/powonline
