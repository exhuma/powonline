from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ErrorType(Enum):
    INVALID_SCHEMA = "invalid-schema"


class TeamState(Enum):
    UNKNOWN = "unknown"
    ARRIVED = "arrived"
    FINISHED = "finished"
    UNREACHABLE = "unreachable"


class AuditType(Enum):
    ADMIN = "admin"
    QUESTIONNAIRE_SCORE = "questionnaire_score"
    STATION_SCORE = "station_score"


class StationRelation(Enum):
    """
    A station-relation defines how one station relates to another.
    """

    PREVIOUS = "previous"
    NEXT = "next"
    UNKNOWN = "unknown"


class TeamStateInfo(BaseModel):
    state: TeamState


class TeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    order: int = 500
    contact: str | None = None
    phone: str | None = None
    comments: str | None = None
    confirmation_key: str = ""
    num_vegetarians: int | None = None
    num_participants: int | None = None
    planned_start_time: datetime | None = None
    effective_start_time: datetime | None = None
    cancelled: bool = False
    is_confirmed: bool = False
    accepted: bool = False
    completed: bool = False
    inserted: datetime | None = None
    updated: datetime | None = None
    finish_time: datetime | None = None
    route_name: str | None = None
    email: EmailStr = ""


class StationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    contact: str | None = None
    phone: str | None = None
    is_start: bool = False
    is_end: bool = False
    order: int = 500


class RouteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    color: str = ""

    @field_validator("color", mode="before")
    @classmethod
    def coerce_none_color(cls, v: object) -> str:
        return v if v is not None else ""


class TimeRange(BaseModel):
    """Represents a time range with inclusive start and exclusive end."""

    start: datetime
    end: datetime

    @field_validator("end")
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        if "start" in info.data and v <= info.data["start"]:
            raise ValueError("end must be greater than start")
        return v


class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    title: str | None = None
    has_favicon: bool = False
    time_range: TimeRange
    inserted: datetime | None = None
    updated: datetime | None = None

    @field_validator("time_range", mode="before")
    @classmethod
    def convert_range_to_timerange(cls, v):
        """Convert SQLAlchemy Range object to TimeRange model."""
        if isinstance(v, dict):
            # Already a dict from API request
            return v
        # SQLAlchemy Range object from database
        if hasattr(v, "lower") and hasattr(v, "upper"):
            return TimeRange(start=v.lower, end=v.upper)
        return v


class EventCreateSchema(BaseModel):
    name: str
    title: str | None = None
    time_range: TimeRange


class EventUpdateSchema(BaseModel):
    name: str | None = None
    title: str | None = None
    time_range: TimeRange | None = None


class EventMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_name: str
    role_name: str


class EventMemberUpdateSchema(BaseModel):
    user_name: str
    role_name: str


class EventDomainSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_id: int
    domain: str


class EventDomainCreateSchema(BaseModel):
    domain: str


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    active: bool = False
    email: str | None = None
    avatar_url: str = ""
    confirmed_at: datetime | None = None
    inserted: datetime | None = None
    updated: datetime | None = None


class UserSchemaSensitive(UserSchema):
    password: str


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class JobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    action: str
    args: dict[str, Any]


class UserSchemaLeaky(UserSchema):
    model_config = ConfigDict(from_attributes=True)
    password: str = ""


class QuestionnaireSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    max_score: int = 0
    order: int = 0

    @field_validator("max_score", mode="before")
    @classmethod
    def coerce_none_max_score(cls, v: object) -> int:
        return 0 if v is None else v

    station_name: str | None = None
    inserted: datetime | None = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    updated: datetime | None = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )


class AssignmentMap(BaseModel, frozen=True):
    teams: dict[str, list[TeamSchema]]
    stations: dict[str, list[StationSchema]]


class AuditLogEntry(BaseModel, frozen=True):
    timestamp: datetime
    username: str
    type: str
    message: str


class DashboardRow(BaseModel, frozen=True):
    team: str
    state: TeamState
    score: int
    updated: datetime | None


class GlobalDashboardStation(BaseModel, frozen=True):
    name: str
    score: int
    state: TeamState


class GlobalDashboardRow(BaseModel, frozen=True):
    team: str
    stations: list[GlobalDashboardStation]


class UploadSchema(BaseModel, frozen=True):
    uuid: UUID
    href: str
    thumbnail: str
    tiny: str
    name: str
    when: datetime


class PasswordCredentials(BaseModel, frozen=True):
    username: str
    password: str


class ErrorMessage(BaseModel, frozen=True):
    message: str
    detail: str = ""


class ListResult[T](BaseModel, frozen=True):
    items: list[T]


class SessionInfo(BaseModel, frozen=True):
    """Returned after a successful login or session check."""

    user: str
    roles: list[str]


class AuthProvider(BaseModel, frozen=True):
    """Describes an available OAuth identity provider."""

    name: str
    label: str
