import fabric.api as fab

fab.env.roledefs = {
    'prod': ['powonline@95.85.17.57'],
}


@fab.task
def develop():
    l = fab.local
    l('[ -d env ] || pyvenv env')
    l('./env/bin/pip install -e .[dev,test]')


@fab.roles('prod')
@fab.task
def deploy():
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
