import fabric.api as fab

fab.env.roledefs = {
    'prod': ['powonline@95.85.17.57'],
    'staging': ['192.168.1.2'],
}

DEPLOY_DIR = '/opt/powonline'


@fab.task
def develop():
    l = fab.local
    l('[ -d env ] || pyvenv env')
    l('./env/bin/pip install -e .[dev,test]')


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
                    '-t exhuma/powonline:latest '
                    '-t exhuma/powonline:%s '
                    '.' % version)
    finally:
        fab.run('rm -rf %s' % tmpdir)

    fab.sudo('install -o %s -d %s' % (fab.env.user, DEPLOY_DIR))
    fab.put('run-prod.sh', DEPLOY_DIR)


@fab.task
def run():
    fab.local('./env/bin/python autoapp.py')
