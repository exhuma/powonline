import logging
from os.path import basename, dirname, join
from time import time

import jwt
import psycopg2
from flask import (Blueprint, current_app, jsonify, make_response, redirect,
                   render_template, request, session, url_for)
from requests_oauthlib import OAuth2Session
from sqlalchemy.exc import IntegrityError

from .core import User, questionnaire_scores
from .exc import AccessDenied
from .model import DB
from .social import Social
from .util import allowed_file, get_user_identity

rootbp = Blueprint('rootbp', __name__)

LOG = logging.getLogger(__name__)
DEFAULT_ALLOWED_ORIGINS = {
    'https://localhost:8080'
}


@rootbp.app_errorhandler(AccessDenied)
def handle_access_errors(error):
    return 'Access Denied', 403


@rootbp.after_app_request
def after_app_request(response):
    try:
        DB.session.commit()
    except:
        LOG.exception('Unable to store data in the DB')
        response = make_response('Internal Server Error!', 500)
        DB.session.rollback()

    cfg_data = current_app.localconfig.get(
        'app', 'allowed_origins', fallback='')
    elements = {line.strip() for line in cfg_data.splitlines() if line.strip()}
    allowed_origins = elements or DEFAULT_ALLOWED_ORIGINS
    LOG.debug('Allowed CORS origins: %r', allowed_origins)

    origin = request.headers.get('Origin', '')
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    elif origin:
        LOG.error('Unauthorized CORS request from %r', origin)

    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE')
    return response


@rootbp.route('/questionnaire-scores')
def get_team_station_questionnaire():
    # TODO this is a quick hack to get finished in time. This route should move
    # TODO Questionnaires should not be linked to stations
    #      This is a simplifcation for the UI for now: no manual selection of
    #      the questionnaire by users.
    output = questionnaire_scores(current_app.localconfig, DB.session)
    return jsonify(output)


@rootbp.route("/social-login/<provider>")
def social_login(provider):
    client = Social.create(current_app.localconfig, provider)
    if not client:
        return '%s is not supported for login!' % provider
    authorization_url, state = client.process_login()
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return jsonify({
        "authorization_url": authorization_url
    })


@rootbp.route("/connect/<provider>")
def callback(provider):
    client = Social.create(current_app.localconfig, provider)
    if not client:
        return '%s is not supported for login!' % provider
    user_info = client.get_user_info(session['oauth_state'], request.url)
    return jsonify(user_info)


@rootbp.route('/login', methods=['POST'])
def login():
    user = None
    data = request.get_json()
    if 'social_provider' in data:
        provider = data['social_provider']
        token = data['token']
        user_id = data['user_id']
        client = Social.create(current_app.localconfig, provider)
        if not client:
            return ("Social provider %r not available (either not supported "
                    "or not fully configured on the back-end)."), 500
        user_info = client.get_user_info_simple(token)
        if user_info:
            user = User.by_social_connection(
                DB.session,
                provider,
                user_id,
                {
                    'display_name': user_info['name'],
                    'avatar_url': user_info['picture'],
                    'email': user_info.get('email')
                }
            )
        else:
            return 'Access Denied', 401
    else:
        username = data['username']
        password = data['password']
        user = User.get(DB.session, username)
        if not user or not user.checkpw(password):
            return 'Access Denied', 401

    if not user:
        return 'Access Denied', 401

    roles = {role.name for role in user.roles}
    # JWT token expiration time (in seconds). Default: 2 hours
    jwt_lifetime = int(current_app.localconfig.get(
        'security', 'jwt_lifetime', default=(2 * 60 * 60)))

    now = int(time())
    payload = {
        'username': user.name,
        'roles': list(roles),
        'iat': now,
        'exp': now + jwt_lifetime
    }
    jwt_secret = current_app.localconfig.get('security', 'jwt_secret')
    result = {
        'token': jwt.encode(payload, jwt_secret).decode('ascii'),
        'roles': list(roles),  # convenience for the frontend
        'user': user.name,  # convenience for the frontend
    }
    return jsonify(result)


@rootbp.route('/')
def index():
    return render_template('index.html')


@rootbp.route('/login/renew', methods=['POST'])
def renew_token():
    data = request.get_json()
    current_token = data['token']
    jwt_secret = current_app.localconfig.get('security', 'jwt_secret')
    # JWT token expiration time (in seconds). Default: 2 hours
    jwt_lifetime = int(current_app.localconfig.get(
        'security', 'jwt_lifetime', default=(2 * 60 * 60)))
    try:
        token_info = jwt.decode(current_token, jwt_secret)
    except jwt.InvalidTokenError as exc:
        LOG.debug('Renewal of invalid token: %s', exc)
        return 'Invalid Token!', 400

    now = int(time())
    new_payload = {
        'username': token_info['username'],
        'roles': token_info['roles'],
        'iat': now,
        'exp': now + jwt_lifetime
    }
    new_token = jwt.encode(new_payload, jwt_secret).decode('ascii')
    return jsonify({'token': new_token})
