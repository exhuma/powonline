from os.path import exists

from gouge.colourcli import Simple
from powonline.config import default
from powonline.util import colorize_werkzeug
from powonline.web import make_app

Simple.basicConfig(level=0)
config = default()
colorize_werkzeug()

if not exists('cert.cert'):
    print("You don't seem to have a SSL cert available for the dev server")
    print('The following commands should allow you to create one')
    print('''
    openssl req -new > new.ssl.csr
    openssl rsa -in privkey.pem -out key.key
    openssl x509 -in new.ssl.csr -out cert.cert -req -signkey key.key -days 365
    ''')
else:
    SSL = ('cert.cert', 'key.key')
    APP = make_app(config)
    APP.run(debug=True, host='0.0.0.0', ssl_context=SSL)
