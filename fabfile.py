import fabric.api as fab

DOCKER_HOST_01 = '195.201.33.98'
DOCKER_HOST_02 = '195.201.226.98'

fab.env.roledefs = {
    'prod': [DOCKER_HOST_01],
    'staging': ['192.168.1.2'],
}

DEPLOY_DIR = '/opt/powonline'


@fab.task
def develop():
    fab.local('[ -d env ] || pyvenv env')
    fab.local('./env/bin/pip install -e .[dev,test]')


@fab.task
def build(with_docker_image=True):
    fab.local('rm -rf dist')
    fab.local('python setup.py sdist')
    if with_docker_image:
        version = fab.local('python setup.py --version', capture=True)
        fullname = fab.local('python setup.py --fullname', capture=True)
        fab.local('cp dist/%s.tar.gz dist.tar.gz' % fullname)
        fab.local('docker build '
                  '-t exhuma/powonline-api:latest '
                  '-t exhuma/powonline-api:%s '
                  '.' % version)
        fab.local('rm dist.tar.gz')


@fab.task
def deploy_database():
    version = fab.local('python setup.py --version', capture=True)
    tmpdir = fab.run('mktemp -d')
    fab.put('database', tmpdir)
    try:
        with fab.cd('%s/database' % tmpdir):
            fab.run('docker build '
                    '-t exhuma/powonline-db:latest '
                    '-t exhuma/powonline-db:%s '
                    '.' % version)
    finally:
        fab.run('rm -rf %s' % tmpdir)


@fab.task
def deploy():
    fab.execute(build, with_docker_image=False)
    fullname = fab.local('python setup.py --fullname', capture=True)
    version = fab.local('python setup.py --version', capture=True)
    tmpdir = fab.run('mktemp -d')
    fab.put('dist/%s.tar.gz' % fullname, '%s/dist.tar.gz' % tmpdir)
    fab.put('Dockerfile', tmpdir)
    fab.put('app.ini.dist', tmpdir)
    fab.put('docker-entrypoint', tmpdir)
    fab.put('set_config', tmpdir)
    fab.put('powonline.wsgi', tmpdir)
    try:
        with fab.cd(tmpdir):
            fab.run('docker build '
                    '-t exhuma/powonline-api:latest '
                    '-t exhuma/powonline-api:%s '
                    '.' % version)
    finally:
        fab.run('rm -rf %s' % tmpdir)

    exists = fab.run('[ -d %s ] && echo 1 || echo 0' % DEPLOY_DIR).strip()
    if exists == '0':
        fab.sudo('install -o %s -d %s' % (fab.env.user, DEPLOY_DIR))

    fab.put('run-api.sh', '%s/run-api.sh.dist' % DEPLOY_DIR)

    fab.run('docker stop powonline-api')
    fab.run('docker rm powonline-api')
    with fab.cd(DEPLOY_DIR):
        fab.run('bash run-api.sh')


@fab.task
def run():
    fab.local('./env/bin/python autoapp.py')
