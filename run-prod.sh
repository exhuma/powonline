#!/bin/bash
docker run \
    -d \
    --expose \
    --volume powonline-api-config:/etc/mamerwiselen/powonline \
    --env DSN=postgresql://powonline@powonline-db/powonline \
    --env VIRTUAL_HOST=powonline-api.albert.lu \
    --env VIRTUAL_PROTO=uwsgi \
    --env LETSENCRYPT_HOST=powonline-api.albert.lu \
    --env LETSENCRYPT_EMAIL=michel@albert.lu \
    exhuma/powonline-api:latest
