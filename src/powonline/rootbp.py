import logging
from os.path import basename, dirname, join
from time import time
from typing import TYPE_CHECKING, cast

import jwt
from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound

from .core import User, questionnaire_scores
from .exc import AccessDenied, PowonlineException, UserInputError
from .httputil import add_cors_headers
from .model import DB, Route, Station
from .social import Social
from .util import allowed_file, get_user_identity

if TYPE_CHECKING:
    from powonline.web import MyFlask

rootbp = Blueprint("rootbp", __name__)

LOG = logging.getLogger(__name__)


@rootbp.app_errorhandler(AccessDenied)
def handle_access_errors(error):
    return "Access Denied", 403


@rootbp.app_errorhandler(UserInputError)
def handle_value_error(error):
    return str(error), 400


@rootbp.app_errorhandler(NotFound)
def handle_not_found(error):
    LOG.info(error)
    return str(error), 404


@rootbp.app_errorhandler(Exception)
def handle_unhandled_exceptions(error):
    LOG.exception(error)
    return "Internal Server Error", 500


@rootbp.app_errorhandler(PowonlineException)
def handle_app_error(error):
    LOG.error(error)
    return str(error), 500


@rootbp.after_app_request
def after_app_request(response):
    try:
        DB.session.commit()
    except:
        LOG.exception("Unable to store data in the DB")
        response = make_response("Internal Server Error!", 500)
        DB.session.rollback()

    add_cors_headers(response)
    return response


@rootbp.route("/questionnaire-scores")
def get_team_station_questionnaire():
    # TODO this is a quick hack to get finished in time. This route should move
    # TODO Questionnaires should not be linked to stations
    #      This is a simplifcation for the UI for now: no manual selection of
    #      the questionnaire by users.
    app = cast("MyFlask", current_app)
    output = questionnaire_scores(DB.session)
    return jsonify(output)


@rootbp.route("/social-login/<provider>")
def social_login(provider):
    app = cast("MyFlask", current_app)
    client = Social.create(app.localconfig, provider)
    if not client:
        return "%s is not supported for login!" % provider
    authorization_url, state = client.process_login()
    # State is used to prevent CSRF, keep this for later.
    session["oauth_state"] = state
    return jsonify({"authorization_url": authorization_url})


@rootbp.route("/connect/<provider>")
def callback(provider):
    app = cast("MyFlask", current_app)
    client = Social.create(app.localconfig, provider)
    if not client:
        return "%s is not supported for login!" % provider
    user_info = client.get_user_info(session["oauth_state"], request.url)
    return jsonify(user_info)


@rootbp.route("/login", methods=["POST"])
def login():
    user = None
    data = request.get_json()
    if "social_provider" in data:
        provider = data["social_provider"]
        token = data["token"]
        user_id = data["user_id"]
        app = cast("MyFlask", current_app)
        client = Social.create(app.localconfig, provider)
        if not client:
            return (
                "Social provider %r not available (either not supported "
                "or not fully configured on the back-end)."
            ), 500
        user_info = client.get_user_info_simple(token)
        if user_info:
            user = User.by_social_connection(
                DB.session,
                provider,
                user_id,
                {
                    "display_name": user_info["name"],
                    "avatar_url": user_info["picture"],
                    "email": user_info.get("email"),
                },
            )
        else:
            return "Access Denied", 401
    else:
        username = data["username"]
        password = data["password"]
        user = User.get(DB.session, username)
        if not user or not user.checkpw(password):
            return "Access Denied", 401

    if not user:
        return "Access Denied", 401

    roles = {role.name for role in user.roles or []}
    # JWT token expiration time (in seconds). Default: 2 hours
    app = cast("MyFlask", current_app)
    jwt_lifetime = int(
        app.localconfig.get("security", "jwt_lifetime", fallback=(2 * 60 * 60))
    )

    now = int(time())
    payload = {
        "username": user.name,
        "roles": list(roles),
        "iat": now,
        "exp": now + jwt_lifetime,
    }
    app = cast("MyFlask", current_app)
    jwt_secret = app.localconfig.get("security", "jwt_secret")
    result = {
        "token": jwt.encode(payload, jwt_secret),
        "roles": list(roles),  # convenience for the frontend
        "user": user.name,  # convenience for the frontend
    }
    return jsonify(result)


@rootbp.route("/")
def index():
    return render_template("index.html")


@rootbp.route("/routeStations", methods=["PUT"])
def setRouteStations():
    payload = request.json
    if payload is None:
        return jsonify({"error": "no payload"}), 400
    query = DB.session.query(Station).filter(
        Station.name == payload["stationName"]
    )
    station = query.one_or_none()
    if not station:
        return jsonify({"error": "no such station"}), 404
    station.routes.clear()
    for routeName in payload["routeNames"]:
        query = DB.session.query(Route).filter(Route.name == routeName)
        station.routes.add(query.one())
    return jsonify(
        {
            "stationName": payload["stationName"],
            "routeNames": payload["routeNames"],
        }
    )


@rootbp.route("/login/renew", methods=["POST"])
def renew_token():
    data = request.get_json()
    current_token = data["token"]
    app = cast("MyFlask", current_app)
    jwt_secret = app.localconfig.get("security", "jwt_secret")
    # JWT token expiration time (in seconds). Default: 2 hours
    jwt_lifetime = int(
        app.localconfig.get("security", "jwt_lifetime", fallback=(2 * 60 * 60))
    )
    try:
        token_info = jwt.decode(current_token, jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        LOG.debug("Renewal of invalid token: %s", exc)
        return "Invalid Token!", 400

    now = int(time())
    new_payload = {
        "username": token_info["username"],
        "roles": token_info["roles"],
        "iat": now,
        "exp": now + jwt_lifetime,
    }
    new_token = jwt.encode(new_payload, jwt_secret)
    return jsonify({"token": new_token})
