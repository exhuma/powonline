from uuid import uuid4
from datetime import datetime, timezone
from powonline.domain.registration import Team, Event, TimeSlot


def test_team_registers_for_event():
    event = Event(
        id=uuid4(),
        name="Test Event",
        time_slot=TimeSlot(
            start=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end=datetime(2020, 1, 1, tzinfo=timezone.utc),
        ),
    )
    team = Team(id=uuid4(), name="Example Team", email="team@example.com")
    event.register(team)
    assert len(event.teams) == 1

def test_team_deregisters_from_event():
    team = Team(id=uuid4(), name="Example Team", email="team@example.com")
    event = Event(
        id=uuid4(),
        name="Test Event",
        time_slot=TimeSlot(
            start=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end=datetime(2020, 1, 1, tzinfo=timezone.utc),
        ),
        teams={team}
    )
    event.deregister(team)
    assert len(event.teams) == 0

def test_unknownteam_deregisters_from_event():
    known_team = Team(id=uuid4(), name="Known Team", email="team@example.com")
    unknown_team = Team(id=uuid4(), name="Unknown Team", email="unknown@example.com")
    event = Event(
        uuid4(),
        name="Test Event",
        time_slot=TimeSlot(
            start=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end=datetime(2020, 1, 1, tzinfo=timezone.utc),
        ),
        teams={known_team}
    )
    event.deregister(unknown_team)
    assert len(event.teams) == 1