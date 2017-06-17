import fabric.api as fab


@fab.task
def develop():
    l = fab.local
    cd = fab.lcd
    with cd('frontend/docker-npm'):
        l('docker build -t exhuma/npm .')
    with cd('frontend/docker-vue'):
        l('docker build -t exhuma/vue .')
    with cd('frontend'):
        l('./npm install')
    l('[ -d env ] || pyvenv env')
    l('./env/bin/pip install -e .')
