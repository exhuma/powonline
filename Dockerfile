FROM python:3-slim
# the PKGFILE should be the *basename* of the python dist-file used to build
# this image.
ARG PKGFILE
EXPOSE 9000
RUN apt-get update && apt-get install -y build-essential
RUN python3 -m venv /opt/powonline
RUN /opt/powonline/bin/pip install -U pip
RUN /opt/powonline/bin/pip install -U setuptools
RUN /opt/powonline/bin/pip install alembic uwsgi
RUN mkdir -p /etc/mamerwiselen/powonline
ADD app.ini.dist /etc/mamerwiselen/powonline/app.ini
ADD docker-entrypoint /
ADD set_config /
RUN chmod +x /docker-entrypoint
RUN useradd -ms /bin/bash powonline
VOLUME ["/etc/mamerwiselen/powonline"]

COPY dist/${PKGFILE} /tmp/
ADD powonline.wsgi /opt/powonline
RUN /opt/powonline/bin/pip install /tmp/${PKGFILE}
RUN /opt/powonline/bin/pip install requests
CMD ["/docker-entrypoint"]
