#!/usr/bin/env python
import logging

from powonline.config import default
from powonline.web import make_app

logging.basicConfig(level=logging.DEBUG)

config = default()
application = make_app(config)
# vim: set ft=python :
