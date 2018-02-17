from config_resolver import Config

from powonline.web import make_app

config = Config('mamerwiselen', 'powonline', version='1.0')
application = make_app(config)
