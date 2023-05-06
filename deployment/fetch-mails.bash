#!/bin/bash
set +xe
while true; do
    /opt/powonline/bin/flask fetch-mails || echo "Unexpected Error"
    sleep 3s;
done
