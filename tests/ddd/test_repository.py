from datetime import datetime
import uuid
from powonline.domain import repository
from powonline.domain import registration


class FakeTeamRepository(repository.AbstractTeamRepository):

    def __init__(self, data: dict[uuid.UUID, registration.Team]) -> None:
        self.data = data

    def get(self, id: uuid.UUID) -> registration.Team | None:
        return self.data.get(id)

    def add(self, team: registration.Team) -> None:
        self.data[team.id] = team


class FakeEventRepository(repository.AbstractEventRepository):

    def __init__(self, data: dict[uuid.UUID, registration.Event]) -> None:
        self.data = data

    def get(self, id: uuid.UUID) -> registration.Event | None:
        return self.data.get(id)

    def add(self, event: registration.Event) -> None:
        self.data[event.id] = event


def test_add_team():
    team = registration.Team(
        id=uuid.uuid4(),
        name="test-team",
        email="example-team@example.com",
    )
    data = {}
    repo = FakeTeamRepository(data)
    repo.add(team)
    assert len(data) == 1
    assert data[team.id] == team


def test_get_team():
    team = registration.Team(
        id=uuid.UUID(int=1),
        name="test-team",
        email="example-team@example.com",
    )
    repo = FakeTeamRepository({})
    repo.add(team)
    result = repo.get(uuid.UUID(int=1))
    assert result == team


def test_add_event():
    event = registration.Event(
        id=uuid.uuid4(),
        name="test-event",
        time_slot=registration.TimeSlot(
            start=datetime(2020, 1, 1), end=datetime(2020, 1, 2)
        ),
    )
    data = {}
    repo = FakeEventRepository(data)
    repo.add(event)
    assert len(data) == 1
    assert data[event.id] == event


def test_get_event():
    event = registration.Event(
        id=uuid.UUID(int=1),
        name="test-event",
        time_slot=registration.TimeSlot(
            start=datetime(2020, 1, 1), end=datetime(2020, 1, 2)
        ),
    )
    repo = FakeEventRepository({})
    repo.add(event)
    result = repo.get(uuid.UUID(int=1))
    assert result == event
