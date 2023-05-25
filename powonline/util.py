import logging
import re
from os.path import splitext

import jwt
from flask import current_app

from .exc import AccessDenied

P_REQUEST_LOG = re.compile(r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+|-)$')

LOG = logging.getLogger("werkzeug")
PERMISSION_MAP = {
    "admin": {
        "admin_files",
        "admin_routes",
        "admin_stations",
        "admin_teams",
        "manage_permissions",
        "manage_station",
        "view_audit_log",
        "view_team_contact",
    },
    "staff": {
        "view_team_contact",
    },
    "station_manager": {
        "manage_station",
    },
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


def allowed_file(filename):
    name, ext = splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


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


def get_user_identity(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        LOG.debug("No Authorization header present!")
        raise AccessDenied('Access Denied (no "Authorization" header passed)!')
    method, _, token = auth_header.partition(" ")
    method = method.lower().strip()
    token = token.strip()
    if method != "bearer" or not token:
        LOG.debug("Authorization header does not provide " "a bearer token!")
        raise AccessDenied("Access Denied (not a bearer token)!")
    try:
        jwt_secret = current_app.localconfig.get("security", "jwt_secret")
        auth_payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
    except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError):
        LOG.info("Bearer token seems to have been tampered with!")
        raise AccessDenied("Access Denied (invalid token)!")

    return auth_payload


def get_user_permissions(request):
    auth_payload = get_user_identity(request)
    # Expand the user roles to permissions, collecting them all in one
    # big set.
    user_roles = set(auth_payload.get("roles", []))
    LOG.debug("Bearer token with the following roles: %r", user_roles)
    all_permissions = set()
    for role in user_roles:
        all_permissions |= PERMISSION_MAP.get(role, set())

    LOG.debug(
        "Bearer token grants the following permissions: %r", all_permissions
    )
    return auth_payload, all_permissions
