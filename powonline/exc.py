class PowonlineException(Exception):
    pass


class NoQuestionnaireForStation(PowonlineException):
    pass


class NoSuchQuestionnaire(PowonlineException):
    pass
