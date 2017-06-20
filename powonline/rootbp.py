import logging

from flask import Blueprint, g

rootbp = Blueprint('rootbp', __name__)

LOG = logging.getLogger(__name__)


@rootbp.before_app_request
def before_app_request():
    from sqlalchemy.orm import sessionmaker, scoped_session
    from .model import ENGINE
    Session = scoped_session(sessionmaker(bind=ENGINE))
    g.session = Session()


@rootbp.after_app_request
def after_app_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE')
    try:
        g.session.commit()
    except:
        LOG.exception('Error when committing to DB')
        g.session.rollback()

    return response
