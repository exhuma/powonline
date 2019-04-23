from config_resolver import Config
from gouge.colourcli import Simple
from powonline.config import default
from powonline.util import colorize_werkzeug
from powonline.web import make_app

Simple.basicConfig(level=0)
config = default()
colorize_werkzeug()


SSL = ('cert.cert', 'key.key')
APP = make_app(config)
APP.run(debug=True, host='0.0.0.0', ssl_context=SSL)
