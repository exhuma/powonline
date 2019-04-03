from fabric import Connection, task
from invoke.config import Config
from invoke.context import Context

DOCKER_HOST_01 = '195.201.33.98'
DOCKER_HOST_02 = '195.201.226.98'
DEPLOY_DIR = '/opt/powonline'
ROLEDEFS = {
    'prod': DOCKER_HOST_01,
    'staging': '192.168.1.2',
}


@task
def develop(ctx):  # type: ignore
    ctx.run('[ -d env ] || pyvenv env')
    ctx.run('./env/bin/pip install -e .[dev,test]')


@task
def build(ctx, with_docker_image=True):  # type: ignore
    ctx.run('rm -rf dist')
    ctx.run('python setup.py sdist')
    if with_docker_image:
        version = ctx.run('python setup.py --version').stdout.strip()
        fullname = ctx.run('python setup.py --fullname').stdout.strip()
        ctx.run('cp dist/%s.tar.gz dist.tar.gz' % fullname)
        ctx.run('docker build '
                '-t exhuma/powonline-api:latest '
                '-t exhuma/powonline-api:%s '
                '.' % version)
        ctx.run('rm dist.tar.gz')


def _deploy_database_remotely(conn: Connection) -> None:
    version = conn.local('python setup.py --version').stdout.strip()
    tmpdir = conn.run('mktemp -d')
    conn.put('database', tmpdir)
    try:
        with conn.cd('%s/database' % tmpdir):
            conn.run('docker build '
                    '-t exhuma/powonline-db:latest '
                    '-t exhuma/powonline-db:%s '
                    '.' % version)
    finally:
        conn.run('rm -rf %s' % tmpdir)


@task
def deploy_database(ctx, environment='staging'):  # type: ignore
    with Connection(ROLEDEFS[environment]) as conn:
        _deploy_database_remotely(conn)


def _deploy_remotely(conn: Connection) -> None:
    fullname = conn.local('python setup.py --fullname').stdout.strip()
    version = conn.local('python setup.py --version').stdout.strip()
    tmpdir = conn.run('mktemp -d').stdout.strip()
    conn.put('Dockerfile', tmpdir)
    conn.put('app.ini.dist', tmpdir)
    conn.put('docker-entrypoint', tmpdir)
    conn.put('set_config', tmpdir)
    conn.put('powonline.wsgi', tmpdir)
    try:
        with conn.cd(tmpdir):
            conn.run('docker build '
                    '-t exhuma/powonline-api:latest '
                    '-t exhuma/powonline-api:%s '
                    '.' % version)
    finally:
        conn.run('rm -rf %s' % tmpdir)

    exists = conn.run('[ -d %s ] && echo 1 || echo 0' % DEPLOY_DIR).strip()
    if exists == '0':
        conn.sudo('install -o %s -d %s' % (conn.user, DEPLOY_DIR))

    conn.put('run-api.sh', '%s/run-api.sh.dist' % DEPLOY_DIR)

    with conn.quiet():
        conn.run('docker stop powonline-api')
        conn.run('docker rm powonline-api')
    with conn.cd(DEPLOY_DIR):
        conn.run('bash run-api.sh')


@task
def deploy(ctx, environment='staging'):  # type: ignore
    build(ctx, with_docker_image=False)
    with Connection(ctx[environment].hostname) as conn:
        _deploy_remotely(conn)


@task
def run(ctx):  # type: ignore
    ctx.run('./env/bin/python autoapp.py')
