"""
Helper script to run the app with SSL (auto-detecting certs)
This is used for local development with SSL
"""

import re
from os.path import exists

from gouge.colourcli import Simple

from powonline.config import default
from powonline.main import create_app

APP = create_app()

if not exists("ssl/cert.cert"):
    print("You don't seem to have a SSL cert available for the dev server")
    print("The following commands should allow you to create one")
    print(
        """
        openssl req -new > ssl/new.ssl.csr
        openssl rsa -in ssl/privkey.pem -out ssl/key.key
        openssl x509 -in new.ssl.csr -out ssl/cert.cert -req -signkey ssl/key.key -days 365
        """
    )
    print(80 * "=")
    print("Running without SSL")
    print(80 * "=")
    SSL = None
else:
    print(80 * "=")
    print("Using ssl/cert.cert and ssl/key.key as SSL context")
    print(80 * "=")
    SSL = ("ssl/cert.cert", "ssl/key.key")

APP.run(debug=True, host="0.0.0.0", ssl_context=SSL)
