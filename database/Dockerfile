FROM postgres:10
RUN apt-get update && apt-get install -y python3-venv
RUN python3 -m venv /opt/alembic
RUN /opt/alembic/bin/pip install alembic
RUN /opt/alembic/bin/pip install psycopg2
ADD alembic /alembic-data/alembic
ADD alembic.ini /alembic-data/alembic.ini
ADD init_script/* /docker-entrypoint-initdb.d/
