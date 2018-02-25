import logging
from time import time

from flask import Blueprint, request, jsonify, current_app, render_template
import jwt

from .model import DB
from .core import User

rootbp = Blueprint('rootbp', __name__)

LOG = logging.getLogger(__name__)


@rootbp.after_app_request
def after_app_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE')
    try:
        DB.session.commit()
    except:
        LOG.exception('Error when committing to DB')
        DB.session.rollback()

    return response


@rootbp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.get(DB.session, username)
    if not user or not user.checkpw(password):
        return 'Access Denied', 401

    roles = {role.name for role in user.roles}
    # JWT token expiration time (in seconds). Default: 2 hours
    jwt_lifetime = int(current_app.localconfig.get(
        'security', 'jwt_lifetime', default=(2 * 60 * 60)))

    now = int(time())
    payload = {
        'username': username,
        'roles': list(roles),
        'iat': now,
        'exp': now + jwt_lifetime
    }
    jwt_secret = current_app.localconfig.get('security', 'jwt_secret')
    result = {
        'token': jwt.encode(payload, jwt_secret).decode('ascii'),
        'roles': list(roles),  # convenience for the frontend
        'user': data['username'],  # convenience for the frontend
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
