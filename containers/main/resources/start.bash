#!/bin/bash
set -xe

# Run database migrations before starting the application server.
# Alembic config and migration scripts are copied to /alembic in the image.
cd /alembic
/opt/powonline/bin/alembic upgrade head

exec /opt/powonline/bin/uvicorn \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --host 0.0.0.0 \
    ${UVICORN_ARGS} \
    --factory powonline.main:create_app
