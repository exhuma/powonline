import abc
from uuid import UUID
from powonline.domain import orm
from .registration import Event, Team


class AbstractRepository[T](abc.ABC):

    @abc.abstractmethod
    def get(self, id: UUID) -> T | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def add(self, entity: T) -> None:
        raise NotImplementedError()


class AbstractTeamRepository(AbstractRepository[Team]):
    pass


class AbstractEventRepository(AbstractRepository[Event]):
    pass
