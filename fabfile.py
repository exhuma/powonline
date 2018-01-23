import fabric.api as fab

fab.env.roledefs = {
    'prod': ['powonline@95.85.17.57'],
}


REMOTE_FOLDER = '/var/www/powonline/www'
REMOTE_USER = 'powonline'


@fab.task
def develop():
    l = fab.local
    cd = fab.lcd
    with cd('frontend/powonline'):
        l('npm install')
    l('[ -d env ] || pyvenv env')
    l('./env/bin/pip install -e .[dev,test]')


@fab.task
@fab.roles('prod')
def deploy_frontend():
    with fab.lcd('frontend/powonline'):
        fab.local('npm run build')
        with fab.cd('www/htdocs'):
            fab.put('dist/*', '.')


@fab.task
@fab.roles('prod')
def deploy_backend():
    fab.local('python setup.py sdist')
    fullname = fab.local('python setup.py --fullname', capture=True)
    fab.put('dist/%s.tar.gz' % fullname, '/tmp')
    with fab.cd('www'):
        fab.put('alembic', '.')
        fab.put('alembic.ini', '.')
        fab.run('./env/bin/pip install -U pip')
        fab.run('./env/bin/pip install wheel alembic')
        fab.run('./env/bin/pip install /tmp/%s.tar.gz' % fullname)
        fab.run('./env/bin/alembic upgrade head')
        fab.run('touch wsgi/powonline.wsgi')


@fab.task
def deploy():
    fab.execute(deploy_frontend)
    fab.execute(deploy_backend)
