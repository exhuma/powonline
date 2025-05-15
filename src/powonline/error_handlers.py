import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .exc import AccessDenied, AuthDeniedReason, UserInputError
from .schema import ErrorMessage

LOG = logging.getLogger(__name__)


def handle_access_errors(request: Request, error: AccessDenied):
    output = ErrorMessage(message="Access Denied", detail=str(error))
    match error.reason:
        case AuthDeniedReason.ACCESS_DENIED:
            status_code = 403
        case AuthDeniedReason.NOT_AUTHENTICATED:
            status_code = 401
        case _:
            LOG.error("Unhandled AccessDenied reason: %r", error.reason)
            status_code = 500
    return JSONResponse(output.model_dump(), status_code)


def handle_value_error(request: Request, error: UserInputError):
    output = ErrorMessage(message="User input error", detail=str(error))
    LOG.debug(output)
    return JSONResponse(output.model_dump(), 400)


def handle_unhandled_exceptions(request: Request, exc: Exception) -> Response:
    output = ErrorMessage(message="Internal Server Error")
    LOG.exception(exc)
    return JSONResponse(output.model_dump(), 500)


def register(app: FastAPI) -> None:
    """
    Register the error-handlers with the given app.
    """
    app.exception_handler(AccessDenied)(handle_access_errors)
    app.exception_handler(UserInputError)(handle_value_error)
    app.exception_handler(Exception)(handle_unhandled_exceptions)
