from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


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


class SocialCredentials(BaseModel, frozen=True):
    social_provider: str
    token: str
    user_id: str
    name: str = ""
    email: str = ""
    picture: str = ""


class ErrorMessage(BaseModel, frozen=True):
    message: str
    detail: str = ""


class ListResult[T](BaseModel, frozen=True):
    items: list[T]
