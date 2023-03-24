#!/bin/bash

# -----------------------------------------------------------------------------
#  Apply alembic migrations to the database
#
#  NOTE: This script is intended for the *production* container. The
#  development container does not contain the folder "/opt/powonline". During
#  development, simply execute alembic manually when needed:
#
#      cd database
#      alembic upgrade head
# -----------------------------------------------------------------------------

set -xe
cd /alembic
/opt/powonline/bin/alembic upgrade head
