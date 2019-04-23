FROM python:3
EXPOSE 9000
RUN python3 -m venv /opt/powonline
RUN /opt/powonline/bin/pip install alembic uwsgi
RUN mkdir -p /etc/mamerwiselen/powonline
ADD app.ini.dist /etc/mamerwiselen/powonline/app.ini
ADD docker-entrypoint /
ADD set_config /
RUN chmod +x /docker-entrypoint
RUN useradd -ms /bin/bash powonline
VOLUME ["/etc/mamerwiselen/powonline"]

COPY dist/docker.tar.gz /tmp/
ADD powonline.wsgi /opt/powonline
RUN /opt/powonline/bin/pip install /tmp/docker.tar.gz
CMD ["/docker-entrypoint"]
