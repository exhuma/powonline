from config_resolver import Config

from powonline.web import make_app
from powonline.util import colorize_werkzeug
from gouge.colourcli import Simple

Simple.basicConfig(level=0)
config = Config('mamerwiselen', 'powonline', version='1.3')
colorize_werkzeug()
APP = make_app(config)
APP.run(debug=True, host='0.0.0.0')
