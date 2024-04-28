FROM python:3.12-slim AS build
ADD . /tmp/src
WORKDIR /tmp/src
RUN python3 -m venv /opt/powonline
RUN /opt/powonline/bin/pip install -U pip
RUN /opt/powonline/bin/pip install gunicorn alembic
RUN /opt/powonline/bin/pip install -r requirements.txt
RUN /opt/powonline/bin/pip install --no-deps .

FROM python:3.12-slim
COPY --from=build /opt/powonline /opt/powonline
ADD deployment/start.bash /
ADD deployment/migrate.bash /
ADD deployment/fetch-mails.bash /
ADD database/alembic /alembic/alembic
ADD database/alembic.ini /alembic/alembic.ini
RUN chmod +x /start.bash
RUN chmod +x /migrate.bash
RUN chmod +x /fetch-mails.bash
EXPOSE 8000
ENTRYPOINT ["/start.bash"]


# RUN useradd -ms /bin/bash powonline
