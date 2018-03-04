#!/usr/bin/env python
import logging
from config_resolver import Config
logging.basicConfig(level=logging.DEBUG)

from powonline.web import make_app
config = Config('mamerwiselen', 'powonline', require_load=True)
application = make_app(config)
# vim: set ft=python :
