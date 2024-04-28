#!/bin/bash
docker run \
    -d \
    --expose \
    --name powonline-api
    --volume powonline-api-config:/etc/mamerwiselen/powonline \
    --env POWONLINE_DSN=postgresql+psycopg://powonline@powonline-db/powonline \
    --env VIRTUAL_HOST=powonline-api.albert.lu \
    --env VIRTUAL_PROTO=uwsgi \
    --env LETSENCRYPT_HOST=powonline-api.albert.lu \
    --env LETSENCRYPT_EMAIL=michel@albert.lu \
    exhuma/powonline-api:latest
