"""
Helper script to run the app with SSL (auto-detecting certs)
This is used for local development with SSL
"""

import re
from os.path import exists

from gouge.colourcli import Simple

from powonline.config import default
from powonline.web import make_app

P_REQUEST_LOG = re.compile(r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+|-)$')

def colorize_werkzeug():  # pragma: no cover
    """
    Fetches the werkzeug logger and adds a color filter.

    This is based on "blessings". If it's not available, this is a no-op!
    """

    try:
        from blessings import Terminal  # type: ignore
    except ImportError:
        return

    term = Terminal()
    method_colors = {
        "GET": term.bold_green,
        "POST": term.bold_yellow,
        "PUT": term.bold_blue,
        "DELETE": term.bold_red,
    }

    class WerkzeugColorFilter:  # pragma: no cover
        def filter(self, record):
            match = P_REQUEST_LOG.match(record.msg)
            if match:
                try:
                    ip, date, request_line, status_code, size = match.groups()
                    method = request_line.split(" ")[0]  # key 0 always exists
                    fmt = method_colors.get(method.upper(), term.white)
                    request_line = fmt(request_line)
                    ip = term.blue(ip)
                    date = term.yellow(date)
                    try:
                        status_code_value = int(status_code)
                        if status_code_value >= 500:
                            status_code = term.yellow_on_red(status_code)
                        elif status_code_value >= 400:
                            status_code = term.red(status_code)
                        elif status_code_value >= 300:
                            status_code = term.black_on_yellow(status_code)
                        elif status_code_value >= 200:
                            status_code = term.green(status_code)
                        else:
                            status_code = term.bold_white(status_code)
                    except ValueError:
                        pass
                    record.msg = '%s - - [%s] "%s" %s %s' % (
                        ip,
                        date,
                        request_line,
                        status_code,
                        size,
                    )
                except ValueError:
                    pass
            return record

    logging.getLogger("werkzeug").addFilter(WerkzeugColorFilter())



Simple.basicConfig(level=0)
config = default()
colorize_werkzeug()
APP = make_app(config)

if not exists("cert.cert"):
    print("You don't seem to have a SSL cert available for the dev server")
    print("The following commands should allow you to create one")
    print(
        """
    openssl req -new > new.ssl.csr
    openssl rsa -in privkey.pem -out key.key
    openssl x509 -in new.ssl.csr -out cert.cert -req -signkey key.key -days 365
    """
    )
    print(80 * "=")
    print("Running without SSL")
    print(80 * "=")
    SSL = None
else:
    print(80 * "=")
    print("Using cert.cert and key.keyas SSL context")
    print(80 * "=")
    SSL = ("cert.cert", "key.key")

APP.run(debug=True, host="0.0.0.0", ssl_context=SSL)
