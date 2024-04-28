from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


class ListResponse[T](BaseModel):
    items: list[T]


class TeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: EmailStr
    order: int
    contact: str | None
    phone: str | None
    comments: str | None
    confirmation_key: str
    num_vegetarians: int | None
    num_participants: int | None
    planned_start_time: datetime | None
    effective_start_time: datetime | None
    cancelled: bool = False
    is_confirmed: bool = False
    accepted: bool = False
    completed: bool = False
    inserted: datetime | None = None
    updated: datetime | None = None
    finish_time: datetime | None = None
    route_name: str | None = None


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
