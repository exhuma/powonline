import logging

from flask import Blueprint, request, jsonify
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

    payload = {
        'username': username,
        'roles': list(roles)
    }
    result = {
        'token': jwt.encode(payload, 'secret').decode('ascii'),
        'roles': list(roles)  # convenience for the frontend
    }
    return jsonify(result)
