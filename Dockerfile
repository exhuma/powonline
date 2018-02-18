FROM python:3
EXPOSE 80
RUN pyvenv /opt/powonline
ADD . /tmp/powonline
RUN /opt/powonline/bin/pip install /tmp/powonline
RUN /opt/powonline/bin/pip install gunicorn alembic
RUN mkdir -p /etc/mamerwiselen/powonline
ADD app.ini.dist /etc/mamerwiselen/powonline/app.ini
ADD docker-entrypoint /
RUN chmod +x /docker-entrypoint
VOLUME ["/etc/mamerwiselen/powonline"]
VOLUME ["/templates"]
CMD ["/docker-entrypoint"]
