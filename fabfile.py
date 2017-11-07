import fabric.api as fab
from getpass import getpass

fab.env.roledefs = {
    'prod': ['powonline@95.85.17.57'],
}


REMOTE_FOLDER = '/var/www/powonline/www'
REMOTE_USER = 'powonline'


@fab.task
def develop():
    l = fab.local
    cd = fab.lcd
    with cd('frontend'):
        l('npm install')
    l('[ -d env ] || pyvenv env')
    l('./env/bin/pip install -e .[dev,test]')


@fab.task
@fab.roles('prod')
def deploy_frontend():
    with fab.lcd('frontend'):
        fab.local('npm run build')
        with fab.cd('www/htdocs'):
            fab.put('powonline/dist/*', '.')


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


@fab.task
def set_password():
    '''
    Set password for a user (add user if missing)
    '''
    fab.local('./env/bin/python autoapp.py --set-password')


@fab.task
def run():
    '''
    Run the backend server
    '''
    fab.local('./env/bin/python autoapp.py --run')
