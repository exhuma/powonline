import logging

from flask import Blueprint

from .model import DB

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
