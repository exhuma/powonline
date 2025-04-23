from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class TimeSlot:
    start: datetime
    end: datetime


@dataclass
class Team:
    id: UUID
    name: str
    email: str
    order: int = 500
    cancelled: bool = False
    contact: str | None = None
    phone: str | None = None
    comments: str | None = None
    is_confirmed: bool = False
    confirmation_key: str = ""
    accepted: bool = False
    completed: bool = False
    inserted: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    updated: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    num_vegetarians: int | None = None
    num_participants: int | None = None
    planned_start_time: datetime | None = None
    effective_start_time: datetime | None = None
    finish_time: datetime | None = None
    route_name: str | None = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, Team):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Event:
    id: UUID
    name: str
    time_slot: TimeSlot
    teams: set[Team] = field(default_factory=set)

    def register(self, team: Team) -> None:
        self.teams.add(team)

    def deregister(self, team: Team) -> None:
        if team not in self.teams:
            return
        self.teams.remove(team)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Event):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
