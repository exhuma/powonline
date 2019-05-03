import os

from fabric import Connection, task
from invoke.context import Context
from patchwork.transfers import rsync as rsync_

DOCKER_HOST_01 = '195.201.33.98'
DOCKER_HOST_02 = '195.201.226.98'
DEPLOY_DIR = '/opt/powonline'
ROLEDEFS = {
    'prod': DOCKER_HOST_01,
    'staging': '192.168.1.2',
}


def _safe_put(conn, filename, destination):
    """
    Uploads *filename* to *destination* only if it does not exist.
    """
    exists_cmd = conn.run('[ -f %s ]' % destination, warn=True)
    if exists_cmd.failed:
        conn.put(filename, destination)
    else:
        print('File %r already exists. Will not overwrite!' % destination)


def rsync(ctx, *args, **kwargs):  # type: ignore
    """Ugly workaround for https://github.com/fabric/patchwork/issues/16."""
    ssh_agent = os.environ.get('SSH_AUTH_SOCK', None)
    if ssh_agent:
        ctx.config['run']['env']['SSH_AUTH_SOCK'] = ssh_agent
    return rsync_(ctx, *args, **kwargs)


@task
def build_python_package(ctx):  # type: ignore
    ctx.run('./env/bin/python setup.py sdist')
    fullname = ctx.run('./env/bin/python setup.py --fullname')
    tar_name = 'dist/%s.tar.gz' % fullname.stdout.strip()
    ctx.run('mv %s dist/docker.tar.gz' % tar_name)


@task
def _build_py_remotely(conn, tmpdir):  # type: ignore
    version = conn.local('./env/bin/python setup.py --version')
    with conn.cd(tmpdir):
        conn.run('docker build '
                 '-t exhuma/powonline-api:latest '
                 '-t exhuma/powonline-api:%s '
                 '.' % version.stdout.strip())


@task
def _build_db_remotely(conn, tmpdir):  # type: ignore
    version = conn.local('./env/bin/python setup.py --version')
    with conn.cd(tmpdir):
        conn.run('docker build '
                 '-t exhuma/powonline-db:latest '
                 '-t exhuma/powonline-db:%s '
                 '.' % version.stdout.strip())


@task
def build_docker(ctx, environment='staging'):  # type: ignore
    build_python_package(ctx)

    host = ROLEDEFS[environment]
    with Connection(host) as conn:
        pytmp = conn.run('mktemp -d /tmp/deploy-powonline-be-XXXX').stdout.strip()
        try:
            rsync(conn, 'dist', pytmp)  # type: ignore
            conn.put('Dockerfile', pytmp)
            conn.put('app.ini.dist', pytmp)
            conn.put('set_config', pytmp)
            conn.put('docker-entrypoint', pytmp)
            conn.put('powonline.wsgi', pytmp)
            _build_py_remotely(conn, pytmp)
        finally:
            conn.run('rm -rf %s' % pytmp)

        dbtmp = conn.run('mktemp -d /tmp/deploy-powonline-db-XXXX').stdout.strip()
        try:
            rsync(conn, 'database/', dbtmp)  # type: ignore
            _build_db_remotely(conn, dbtmp)
        finally:
            conn.run('rm -rf %s' % dbtmp)


@task
def deploy(ctx, environment='staging'):  # type: ignore
    build_docker(ctx, environment)
    host = ROLEDEFS[environment]
    with Connection(host) as conn:
        _safe_put(conn,
                  'api.env', '%s/api.env' % DEPLOY_DIR)
        _safe_put(conn,
                  'docker-compose.yaml', '%s/docker-compose.yaml' % DEPLOY_DIR)
        with conn.cd(DEPLOY_DIR):
            conn.run('docker-compose down && docker-compose up -d', pty=True)


@task
def run(ctx):
    ctx.run('./env/bin/python autoapp.py', pty=True)
