class PowonlineException(Exception):
    pass


class NoQuestionnaireForStation(PowonlineException):
    pass


class NoSuchQuestionnaire(PowonlineException):
    pass


class AccessDenied(PowonlineException):
    pass
