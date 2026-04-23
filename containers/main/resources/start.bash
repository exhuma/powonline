#!/bin/bash
set -xe
exec /opt/flightlogs/bin/uvicorn \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --host 0.0.0.0 \
    ${UVICORN_ARGS} \
    --factory powonline.main:create_app
