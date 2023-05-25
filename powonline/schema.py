from dateutil.parser import parse
from marshmallow import Schema, fields  # type: ignore


class FuzzyDate(fields.Field):
    def _serialize(self, value, attr, obj):
        """
        Convert a Python object into an outside-world object
        """
        if not value:
            return None
        return value.isoformat()

    def _deserialize(self, value, attr, obj):
        """
        Convert a outside-world value into a Python object
        """
        if not value:
            return None
        return parse(value)


class TeamSchema(Schema):
    name = fields.String(required=True)
    email = fields.Email()
    order = fields.Int()
    cancelled = fields.Boolean(default=False)
    contact = fields.String()
    phone = fields.String()
    comments = fields.String()
    is_confirmed = fields.Boolean(default=False)
    confirmation_key = fields.String()
    accepted = fields.Boolean(default=False)
    completed = fields.Boolean(default=False)
    inserted = fields.LocalDateTime(missing=None)
    updated = fields.LocalDateTime(allow_none=True)
    num_vegetarians = fields.Int(allow_none=True)
    num_participants = fields.Int(allow_none=True)
    planned_start_time = FuzzyDate(allow_none=True)
    effective_start_time = FuzzyDate(allow_none=True)
    finish_time = FuzzyDate(allow_none=True)
    route_name = fields.String(missing=None)


class StationSchema(Schema):
    name = fields.String(required=True)
    contact = fields.String()
    phone = fields.String()
    is_start = fields.Boolean(default=False)
    is_end = fields.Boolean(default=False)
    order = fields.Int(missing=500, default=500)


class RouteSchema(Schema):
    name = fields.String(required=True)
    color = fields.String(missing=None)


class UserSchema(Schema):
    name = fields.String(required=True)
    password = fields.String()
    email = fields.String()
    inserted = fields.DateTime()
    updated = fields.DateTime()
    email = fields.Str()
    active = fields.Bool()
    confirmed_at = fields.DateTime()
    avatar_url = fields.String()


class RoleSchema(Schema):
    name = fields.String(required=True)


class JobSchema(Schema):
    action = fields.String(required=True)
    args = fields.Dict(required=True)


def make_list_schema(item_schema, exclude=None):
    exclude = exclude or []

    class ListSchema(Schema):
        items = fields.Nested(item_schema, many=True, exclude=exclude)

    return ListSchema()


ROLE_SCHEMA = RoleSchema()
ROUTE_SCHEMA = RouteSchema()
STATION_SCHEMA = StationSchema()
TEAM_SCHEMA = TeamSchema()
USER_SCHEMA = UserSchema()
USER_SCHEMA_SAFE = UserSchema(exclude=["password"])
JOB_SCHEMA = JobSchema()
TEAM_LIST_SCHEMA = make_list_schema(TeamSchema)
STATION_LIST_SCHEMA = make_list_schema(StationSchema)
ROUTE_LIST_SCHEMA = make_list_schema(RouteSchema)
USER_LIST_SCHEMA = make_list_schema(UserSchema, exclude=["password"])
