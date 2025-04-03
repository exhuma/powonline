#!/bin/bash
set -xe
exec /opt/powonline/bin/gunicorn -b "0.0.0.0:8000" "powonline.web:make_app()"
