class PowonlineException(Exception):
    pass


class NoQuestionnaireForStation(PowonlineException):
    def __init__(self, station, msg=""):
        super().__init__(msg or f"No questionnaire for station {station}")
        self.station = station


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
