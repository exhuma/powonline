from powonline.config import default
from powonline.web import make_app

config = default()
application = make_app(config)
