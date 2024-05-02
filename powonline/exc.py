from enum import Enum


class AuthDeniedReason(Enum):
    ACCESS_DENIED = "access_denied"
    NOT_AUTHENTICATED = "not_authenticated"
    UNKNOWN = "unknown"


class PowonlineException(Exception):
    pass


class NotFound(PowonlineException):
    pass


class NoQuestionnaireForStation(NotFound):
    pass


class NoSuchQuestionnaire(NotFound):
    pass


class AccessDenied(PowonlineException):
    reason: AuthDeniedReason = AuthDeniedReason.ACCESS_DENIED

    def __init__(
        self,
        message: str,
        reason: AuthDeniedReason = AuthDeniedReason.ACCESS_DENIED,
    ):
        super().__init__(message)
        self.reason = reason


class ValidationError(PowonlineException):
    pass


class UserInputError(ValidationError):
    """
    Raised for invalid user-input
    """
