#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.DEBUG,
                    filename='/var/www/powonline/www/applog/debug_log')

from powonline.web import make_app
application = make_app('postgresql://powonline@/powonline)  # NOQA
# vim: set ft=python :
