#!/bin/bash
# -----------------------------------------------------------------------------
#  Seed the database with pre-production demo data.
#
#  This script is the container entry-point intended for use by a cronjob
#  managed by Ansible on the pre-prod instance.
#
#  Usage inside a running container:
#    /seed.bash            # idempotent upsert (safe to run at any time)
#    /seed.bash --reset    # wipe all demo-prefixed rows then re-seed
#
#  Typical Ansible cron entry (nightly reset at 02:00):
#    0 2 * * * docker exec <container_name> /seed.bash --reset
#
#  Requirements:
#    - POWONLINE_DSN must be set in the container environment.
#    - The script is NOT intended for the production instance.
# -----------------------------------------------------------------------------

set -e

exec /opt/powonline/bin/python /scripts/seed_demo.py "$@"
