#!/bin/bash

TEST_DB_NAME="powonline_production"
DUMP_FILE="dump-2026-04-22.sql"

DUMP_EXISTS_LOCALLY=$(test -f ${DUMP_FILE} && echo "yes" || echo "no")

if [ "${DUMP_EXISTS_LOCALLY}" = "no" ]; then
    ssh exhuma@monodocker.albert.lu \
        docker exec lost-tracker-data_lost-tracker-db_1 pg_dump \
            -U postgres \
            -a \
            -T alembic_version \
            -T role \
            powonline > ${DUMP_FILE} \
        powonline > ${DUMP_FILE}
fi

psql ${POWONLINE_DSN} -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME}";
psql ${POWONLINE_DSN} -c "CREATE DATABASE ${TEST_DB_NAME}";

# Replace the DB-name from the DSN for the next command
DSN_WITHOUT_DB=$(echo ${POWONLINE_DSN} | sed -E 's/\/[^\/]+$/\//')
TEST_DB_DSN="${DSN_WITHOUT_DB}${TEST_DB_NAME}"

POWONLINE_DSN=${TEST_DB_DSN} uv run alembic upgrade 4e827a0d51ba
psql -X1qf ${DUMP_FILE} --set ON_ERROR_STOP=on ${TEST_DB_DSN}
echo Dumped into ${TEST_DB_DSN}
