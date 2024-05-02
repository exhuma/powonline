import logging

from fastapi import FastAPI, Request, Response

from .exc import AccessDenied, UserInputError

LOG = logging.getLogger(__name__)


def handle_access_errors(error: AccessDenied):
    return "Access Denied", 403


def handle_value_error(error: UserInputError):
    return str(error), 400


def handle_unhandled_exceptions(request: Request, exc: Exception) -> Response:
    LOG.exception(exc)
    return Response("Internal Server Error", status_code=500)


def register(app: FastAPI) -> None:
    """
    Register the error-handlers with the given app.
    """
    app.exception_handler(AccessDenied)(handle_access_errors)
    app.exception_handler(UserInputError)(handle_value_error)
    app.exception_handler(Exception)(handle_unhandled_exceptions)
