#!/bin/bash

# -----------------------------------------------------------------------------
#  Install any additional dependencies into the dev-container that are
#  needed/useful during development
# -----------------------------------------------------------------------------

set -xe

pipx install alembic
pipx inject alembic psycopg2-binary
pipx install fabric
pipx install pre-commit
fab develop

(cd database && alembic upgrade head)
(cd database && alembic show head)
