#!/bin/bash

# -----------------------------------------------------------------------------
#  Install any additional dependencies into the dev-container that are
#  needed/useful during development
# -----------------------------------------------------------------------------

set -xe

suto apt-get update && sudo apt-get install -y entr

pipx install alembic
pipx inject alembic psycopg[binary]
pipx install fabric
pipx inject fabric decorator  # <- fabric bugfix
pipx install pre-commit
fab develop

(cd database && alembic upgrade head)
(cd database && alembic show head)

psql -v ON_ERROR_STOP=1 -X1qf .devcontainer/sample-data.sql postgresql://postgres:postgres@db/powonline
