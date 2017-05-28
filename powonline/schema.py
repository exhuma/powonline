from marshmallow import Schema, fields


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
    inserted = fields.LocalDateTime()
    updated = fields.LocalDateTime()
    num_vegetarians = fields.Int()
    num_participants = fields.Int()
    planned_start_time = fields.LocalDateTime()
    effective_start_time = fields.LocalDateTime()
    finish_time = fields.LocalDateTime()


class StationSchema(Schema):
    name = fields.String(required=True)
    contact = fields.String()
    phone = fields.String()
    is_start = fields.Boolean(default=False)
    is_end = fields.Boolean(default=False)


class RouteSchema(Schema):
    name = fields.String(required=True)


class UserSchema(Schema):
    # TODO: Should the name be the PK? Email or ID would be better.
    name = fields.String(required=True)


class RoleSchema(Schema):
    name = fields.String(required=True)


class JobSchema(Schema):
    action = fields.String(required=True)
    args = fields.Dict(required=True)


ROLE_SCHEMA = RoleSchema()
ROUTE_SCHEMA = RouteSchema()
STATION_SCHEMA = StationSchema()
TEAM_SCHEMA = TeamSchema()
USER_SCHEMA = UserSchema()
JOB_SCHEMA = JobSchema()
