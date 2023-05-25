class PowonlineException(Exception):
    pass


class NoQuestionnaireForStation(PowonlineException):
    pass


class NoSuchQuestionnaire(PowonlineException):
    pass


class AccessDenied(PowonlineException):
    pass


class ValidationError(PowonlineException):
    pass


class UserInputError(ValidationError):
    """
    Raised for invalid user-input
    """
