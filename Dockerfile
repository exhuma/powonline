FROM python:3
EXPOSE 9000
RUN pyvenv /opt/powonline
ADD . /tmp/powonline
ADD powonline.wsgi /opt/powonline
RUN /opt/powonline/bin/pip install /tmp/powonline
RUN /opt/powonline/bin/pip install alembic uwsgi
RUN mkdir -p /etc/mamerwiselen/powonline
ADD app.ini.dist /etc/mamerwiselen/powonline/app.ini
ADD docker-entrypoint /
RUN chmod +x /docker-entrypoint
RUN useradd -ms /bin/bash powonline
VOLUME ["/etc/mamerwiselen/powonline"]
CMD ["/docker-entrypoint"]
