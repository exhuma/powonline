import logging
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from json import JSONEncoder, dumps
from os import makedirs, stat, unlink
from os.path import basename, dirname, join
from typing import TYPE_CHECKING, Any, cast

import jwt
from flask import (
    current_app,
    g,
    jsonify,
    make_response,
    request,
    send_from_directory,
    url_for,
)
from flask_restful import Resource, fields, marshal_with  # type: ignore
from PIL import ExifTags, Image
from werkzeug.utils import secure_filename

from powonline.schema import (
    JobSchema,
    ListResponse,
    RoleSchema,
    RouteSchema,
    StationSchema,
    TeamSchema,
    UserSchema,
)

from . import core
from .core import StationRelation
from .exc import (
    AccessDenied,
    NoQuestionnaireForStation,
    UserInputError,
    ValidationError,
)
from .model import DB, AuditType, TeamState
from .model import AuditLog as DBAuditLog
from .model import Upload as DBUpload
from .util import allowed_file, get_user_identity, get_user_permissions

EXIF_TAGS = ExifTags.TAGS
LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from powonline.web import MyFlask


class ErrorType(Enum):
    INVALID_SCHEMA = "invalid-schema"


def upload_to_json(db_instance: DBUpload) -> dict[str, Any]:
    """
    Convert a DB-instance of an upload to a JSONifiable dictionary
    """
    file_url = url_for(
        "api.get_file", uuid=db_instance.uuid, _external=True, _scheme="https"
    )
    tn_url = url_for(
        "api.get_file",
        uuid=db_instance.uuid,
        size=256,
        _external=True,
        _scheme="https",
    )
    tiny_url = url_for(
        "api.get_file",
        uuid=db_instance.uuid,
        size=64,
        _external=True,
        _scheme="https",
    )

    app = cast("MyFlask", current_app)
    data_folder = app.localconfig.get(  # type: ignore
        "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
    )
    fullname = join(data_folder, db_instance.filename or "")

    try:
        mtime_unix = stat(fullname).st_mtime
    except FileNotFoundError:
        LOG.warning("Missing file %r (was in DB but not on disk)!", fullname)
        return {}
    mtime = datetime.fromtimestamp(mtime_unix, timezone.utc)

    return {
        "uuid": db_instance.uuid,
        "href": file_url,
        "thumbnail": tn_url,
        "tiny": tiny_url,
        "name": basename(db_instance.filename or ""),
        "when": mtime.isoformat(),
    }


def validate_score(value):
    if isinstance(value, str):
        score = int(value, 10) if value.strip() else 0
    else:
        score = value if value else 0
    return score


class require_permissions:
    """
    Decorator for routes.

    All permissions defined in the decorator are required.
    """

    def __init__(self, *permissions):
        self.permissions = set(permissions)

    def __call__(self, f):
        @wraps(f)
        def fun(*args, **kwargs):
            try:
                auth_payload, all_permissions = get_user_permissions(request)
            except AccessDenied as exc:
                return str(exc), 401

            # by removing the users permissions from the required permissions,
            # we will end up with an empty set if the user is granted access.
            # All remaining permissions are those that the user was not granted
            # (the user is missing those permissions to gain entry).
            # Hence, if the resulting set is non-empty, we block access.
            missing_permissions = self.permissions - all_permissions
            if missing_permissions:
                LOG.debug(
                    "User was missing the following permissions: %r",
                    missing_permissions,
                )
                return "Access Denied (Not enough permissions)!", 401

            # Keep a reference to the JWT payload in the "g" object
            g.jwt_payload = auth_payload

            return f(*args, **kwargs)

        return fun


class MyJsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        elif isinstance(o, Enum):
            return o.value
        elif isinstance(o, datetime):
            return o.isoformat()
        super().default(o)


class UserList(Resource):
    @require_permissions("manage_permissions")
    def get(self):
        users = core.User.all(DB.session)
        users = [
            UserSchema.model_dump(UserSchema.model_validate(user))
            for user in users
        ]
        document = ListResponse(items=users).model_dump_json()
        output = make_response(document, 200)
        output.content_type = "application/json"
        return output

    @require_permissions("manage_permissions")
    def post(self):
        data = request.get_json()
        parsed_data = UserSchema.model_validate(data)
        output = core.User.create_new(DB.session, parsed_data)
        return User._single_response(UserSchema.from_orm(output), 201)


class User(Resource):
    @staticmethod
    def _single_response(output, status_code=200):
        document = UserSchema.model_dump_json(output)
        response = make_response(document)
        response.status_code = status_code
        response.content_type = "application/json"
        return response

    @require_permissions("manage_permissions")
    def get(self, name):
        user = core.User.get(DB.session, name)
        if not user:
            return "No such user", 404

        return User._single_response(UserSchema.model_validate(user), 200)

    @require_permissions("manage_permissions")
    def put(self, name):
        data = request.get_json()
        parsed_data = UserSchema.model_validate(data)
        output = core.User.upsert(DB.session, name, parsed_data)
        return User._single_response(UserSchema.model_validate(output), 200)

    @require_permissions("manage_permissions")
    def delete(self, name):
        core.User.delete(DB.session, name)
        return "", 204


class TeamList(Resource):
    def get(self):
        quickfilter = request.args.get("quickfilter", "")
        assigned_to_route = request.args.get("assigned_route", "")
        if quickfilter:
            func_name = "quickfilter_%s" % quickfilter
            filter_func = getattr(core.Team, func_name, None)
            if not filter_func:
                return "%r is not a known quickfilter!" % quickfilter, 400
            teams = filter_func(DB.session)
        elif assigned_to_route:
            teams = core.Team.assigned_to_route(DB.session, assigned_to_route)
        else:
            teams = core.Team.all(DB.session)

        teams = [
            TeamSchema.model_dump(TeamSchema.model_validate(team))
            for team in teams
        ]
        output = ListResponse(items=teams)
        parsed_output = output.model_dump_json()

        output = make_response(parsed_output, 200)
        output.content_type = "application/json"
        return output

    @require_permissions("admin_teams")
    def post(self):
        data = request.get_json()
        parsed_data = TeamSchema.model_validate(data)
        output = core.Team.create_new(DB.session, parsed_data.model_dump())
        return Team._single_response(TeamSchema.model_validate(output), 201)


class Team(Resource):
    @staticmethod
    def _single_response(output, status_code=200):
        parsed_output = TeamSchema.model_dump_json(output)
        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = "application/json"
        return response

    @require_permissions("admin_teams")
    def put(self, name):
        data = request.get_json()
        parsed_data = TeamSchema.model_validate(data)
        output = core.Team.upsert(DB.session, name, parsed_data.model_dump())
        DB.session.flush()

        app = cast("MyFlask", current_app)
        pusher_channel = app.localconfig.get(
            "pusher_channels",
            "team_station_state",
            fallback="team_station_state_dev",
        )
        app = cast("MyFlask", current_app)
        app.pusher.send_team_event("team-details-change", {"name": name})

        return Team._single_response(TeamSchema.model_validate(output), 200)

    @require_permissions("admin_teams")
    def delete(self, name):
        core.Team.delete(DB.session, name)
        app = cast("MyFlask", current_app)
        pusher_channel = app.localconfig.get(
            "pusher_channels",
            "team_station_state",
            fallback="team_station_state_dev",
        )
        app.pusher.send_team_event("team-deleted", {"name": name})
        return "", 204

    def get(self, name):
        team = core.Team.get(DB.session, name)
        if not team:
            return "No such team", 404

        return Team._single_response(TeamSchema.model_validate(team), 200)


class StationList(Resource):
    def get(self):
        items = core.Station.all(DB.session)
        items = [
            StationSchema.model_dump(StationSchema.model_validate(item))
            for item in items
        ]
        parsed_output = ListResponse(items=items).model_dump_json()
        output = make_response(parsed_output, 200)
        output.content_type = "application/json"
        return output

    @require_permissions("admin_stations")
    def post(self):
        data = request.get_json()
        parsed_data = StationSchema.model_validate(data)
        output = core.Station.create_new(DB.session, parsed_data.model_dump())
        return Station._single_response(
            StationSchema.model_validate(output), 201
        )


class Station(Resource):
    @staticmethod
    def _single_response(output: StationSchema, status_code=200):
        parsed_output = StationSchema.model_dump_json(output)
        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = "application/json"
        return response

    def get(self, name, relation=""):
        if relation.strip():
            try:
                parsed_relation = StationRelation[relation.upper()]
            except KeyError:
                raise UserInputError(
                    f"{relation!r} is not a valid station-relation"
                )

            related_station = core.Station.related(
                DB.session, name, parsed_relation
            )
            if not related_station:
                output = make_response('""')
                output.content_type = "application/json"
                return output
            return jsonify(related_station)
        raise NotImplementedError("Not yet implemented")

    @require_permissions("manage_station")
    def put(self, name):
        auth, permissions = get_user_permissions(request)

        if "admin" not in auth["roles"] and not core.User.may_access_station(
            DB.session, auth["username"], name
        ):
            return "Access denied to this station!", 401

        data = request.get_json()
        parsed_data = StationSchema.model_validate(data)
        output = core.Station.upsert(DB.session, name, parsed_data.model_dump())
        return Station._single_response(
            StationSchema.model_validate(output), 200
        )

    @require_permissions("admin_stations")
    def delete(self, name):
        core.Station.delete(DB.session, name)
        return "", 204


class RouteList(Resource):
    def get(self):
        items = list(core.Route.all(DB.session))
        items = [
            RouteSchema.model_dump(RouteSchema.model_validate(item))
            for item in items
        ]
        parsed_output = ListResponse(items=items).model_dump_json()
        output = make_response(parsed_output, 200)
        output.content_type = "application/json"
        return output

    @require_permissions("admin_routes")
    def post(self):
        data = request.get_json()
        parsed_data = RouteSchema.model_validate(data)
        output = core.Route.create_new(DB.session, parsed_data.model_dump())
        return Route._single_response(RouteSchema.model_validate(output), 201)


class Route(Resource):
    @staticmethod
    def _single_response(output, status_code=200):
        parsed_output = RouteSchema.model_dump_json(output)
        response = make_response(parsed_output)
        response.status_code = status_code
        response.content_type = "application/json"
        return response

    @require_permissions("admin_routes")
    def put(self, name):
        data = request.get_json()
        parsed_data = RouteSchema.model_validate(data)
        output = core.Route.upsert(DB.session, name, parsed_data)
        return Route._single_response(RouteSchema.model_validate(output), 200)

    @require_permissions("admin_routes")
    def delete(self, name):
        core.Route.delete(DB.session, name)
        return "", 204


class StationUserList(Resource):
    def _assign_user_to_station(self, station_name):
        data = request.get_json()
        user = UserSchema.model_validate(data)
        success = core.Station.assign_user(DB.session, station_name, user.name)
        if success:
            return "", 204
        else:
            return "Station is already assigned to that user", 400

    def _assign_station_to_user(self, user_name):
        data = request.get_json()
        station = StationSchema.model_validate(data)
        success = core.User.assign_station(DB.session, user_name, station.name)
        if success:
            return "", 204
        else:
            return "Station is already assigned to that user", 400

    def _list_station_by_user(self, user_name):
        user = core.User.get(DB.session, user_name)
        if not user:
            return "No such user", 404
        all_stations = core.Station.all(DB.session)
        user_stations = {station.name for station in user.stations or []}
        output = []
        for station in all_stations:
            output.append((station.name, station.name in user_stations))
        return jsonify(output)

    @require_permissions("manage_permissions")
    def get(self, station_name=None, user_name=None):
        if user_name and not station_name:
            return self._list_station_by_user(user_name)
        elif station_name and not user_name:
            return self._list_user_by_station(station_name)
        else:
            return "Unexpected input!", 400

    @require_permissions("manage_permissions")
    def post(self, station_name=None, user_name=None):
        """
        Assigns a user to a station
        """
        if user_name and not station_name:
            return self._assign_station_to_user(user_name)
        elif station_name and not user_name:
            return self._assign_user_to_station(station_name)
        else:
            return "Unexpected input!", 400


class StationUser(Resource):
    @require_permissions("manage_permissions")
    def get(self, user_name=None, station_name=None):
        user = core.User.get(DB.session, user_name)
        if not user:
            return "No such user", 404
        stations = {_.name for _ in user.stations or []}

        if station_name in stations:
            return jsonify(True)
        else:
            return jsonify(False)

    @require_permissions("manage_permissions")
    def delete(self, station_name, user_name):
        success = core.Station.unassign_user(
            DB.session, station_name, user_name
        )
        if success:
            return "", 204
        else:
            return "Unexpected error!", 500


class RouteTeamList(Resource):
    @require_permissions("admin_routes")
    def post(self, route_name):
        """
        Assign a team to a route
        """
        data = request.get_json()
        if not data:
            return "Payload required!", 400
        team_name = data["name"]

        success = core.Route.assign_team(DB.session, route_name, team_name)
        if success:
            return "", 204
        else:
            return "Team is already assigned to a route", 400


class RouteTeam(Resource):
    @require_permissions("admin_routes")
    def delete(self, route_name, team_name):
        success = core.Route.unassign_team(DB.session, route_name, team_name)
        if success:
            return "", 204
        else:
            return "Unexpected error!", 500


class UserRoleList(Resource):
    @require_permissions("manage_permissions")
    def get(self, user_name):
        user = core.User.get(DB.session, user_name)
        if not user:
            return "No such user", 404
        all_roles = core.Role.all(DB.session)
        user_roles = {role.name for role in user.roles or []}
        output = []
        for role in all_roles:
            output.append((role.name, role.name in user_roles))
        return jsonify(output)

    @require_permissions("manage_permissions")
    def post(self, user_name):
        """
        Assign a role to a user
        """
        data = request.get_json()
        parsed_data = RoleSchema.model_validate(data)
        role_name = parsed_data.name
        success = core.User.assign_role(DB.session, user_name, role_name)
        if success:
            return "", 204
        else:
            return "Unexpected error!", 500


class UserRole(Resource):
    @require_permissions("manage_permissions")
    def delete(self, user_name, role_name):
        success = core.User.unassign_role(DB.session, user_name, role_name)
        if success:
            return "", 204
        else:
            return "Unexpected error!", 500

    @require_permissions("manage_permissions")
    def get(self, user_name, role_name):
        user = core.User.get(DB.session, user_name)
        if not user:
            return "No such user", 404
        roles = {_.name for _ in user.roles or []}

        if role_name in roles:
            return jsonify(True)
        else:
            return jsonify(False)


class RouteStationList(Resource):
    @require_permissions("admin_routes")
    def post(self, route_name):
        """
        Assign a station to a route
        """
        data = request.get_json()
        parsed_data = StationSchema.model_validate(data)
        station_name = parsed_data.name

        success = core.Route.assign_station(
            DB.session, route_name, station_name
        )
        if success:
            return "", 204
        else:
            return "Unexpected error!", 500


class RouteStation(Resource):
    @require_permissions("admin_routes")
    def delete(self, route_name, station_name):
        success = core.Route.unassign_station(
            DB.session, route_name, station_name
        )
        if success:
            return "", 204
        else:
            return "Unexpected error!", 500


class TeamStation(Resource):
    def get(self, team_name, station_name=None):
        if station_name is None:
            items = core.Team.stations(DB.session, team_name)
            parsed_output = ListResponse(
                items=sorted(items, key=lambda x: x.name)
            ).model_dump_json()
            output = make_response(parsed_output, 200)
            output.content_type = "application/json"
            return output
        else:
            state = core.Team.get_station_data(
                DB.session, team_name, station_name
            )
            if state.state:
                return {"state": state.state.value}, 200
            else:
                return {"state": TeamState.UNKNOWN.value}, 200


class Assignments(Resource):
    def get(self):
        data = core.get_assignments(DB.session)

        out_stations = {}
        for route_name, stations in data["stations"].items():
            out_stations[route_name] = [
                StationSchema.model_dump(StationSchema.model_validate(station))
                for station in stations
            ]

        out_teams = {}
        for route_name, teams in data["teams"].items():
            out_teams[route_name] = [
                TeamSchema.model_dump(TeamSchema.model_validate(team))
                for team in teams
            ]

        output = {"stations": out_stations, "teams": out_teams}

        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = "application/json"
        return output


class Scoreboard(Resource):
    """
    Helper resource for the frontend
    """

    def get(self):
        output = list(core.scoreboard(DB.session))
        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = "application/json"
        return output


class Dashboard(Resource):
    """
    Helper resource for the frontend
    """

    def get(self, station_name, relation=""):
        if relation.strip():
            try:
                parsed_relation = StationRelation[relation.upper()]
            except KeyError:
                raise UserInputError(
                    f"{relation!r} is not a valid station-relation"
                )

            station_name = core.Station.related(
                DB.session, station_name, parsed_relation
            )
            if not station_name:
                output = make_response("[]")
                output.content_type = "application/json"
                return output

        output = []
        for team_name, state, score, updated in core.Station.team_states(
            DB.session, station_name
        ):
            output.append(
                {
                    "team": team_name,
                    "state": state.value,
                    "score": score,
                    "updated": updated,
                }
            )

        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = "application/json"
        return output


class GlobalDashboard(Resource):
    """
    The global state of each team on each station of the event.
    """

    def get(self):
        output = core.global_dashboard(DB.session)
        output = make_response(dumps(output, cls=MyJsonEncoder), 200)
        output.content_type = "application/json"
        return output


class RouteColor(Resource):
    """
    A direct route to the route color
    """

    @require_permissions("admin_stations")
    def put(self, route_name):
        """
        Replaces the route color with a new color
        """
        data = request.get_json()
        new_color = data["color"]
        output = core.Route.update_color(DB.session, route_name, new_color)
        DB.session.commit()
        return jsonify({"color": new_color})


class UploadList(Resource):
    """
    A list of the current user's uploaded files
    """

    def post(self):
        app = cast("MyFlask", current_app)
        data_folder = app.localconfig.get(
            "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
        )
        identity = get_user_identity(request)

        if "file" not in request.files:
            return "No file received", 400

        fileobj = request.files["file"]
        if fileobj.filename == "":
            return "No file selected", 400

        if fileobj and fileobj.filename and allowed_file(fileobj.filename):
            filename = secure_filename(fileobj.filename)
            try:
                makedirs(join(data_folder, identity["username"]))
            except FileExistsError:
                pass
            relative_target = join(identity["username"], filename)
            target = join(data_folder, relative_target)
            fileobj.save(target)

            db_instance = (
                DB.session.query(DBUpload)
                .filter_by(
                    filename=relative_target, username=identity["username"]
                )
                .one_or_none()
            )

            if not db_instance:
                db_instance = DBUpload(relative_target, identity["username"])
                DB.session.add(db_instance)
                DB.session.flush()

            response = make_response("OK")
            event_object = upload_to_json(db_instance)
            response.headers["Location"] = event_object["href"]
            response.status_code = 201
            app.pusher.send_file_event("file-added", event_object)
            return response
        return "The given file is not allowed", 400

    def _get_public(self):
        """
        Return files for a public request (f.ex. image gallery)
        """
        output = []
        files = core.Upload.all(DB.session)
        for item in files:
            json_data = upload_to_json(item)
            if json_data:
                output.append(json_data)
        return jsonify(output)

    def _get_private(self):
        """
        Return files for a private request (f.ex. manageing uploads)
        """
        identity, all_permissions = get_user_permissions(request)
        output = {}
        if "admin_files" in all_permissions:
            files = core.Upload.all(DB.session)
            for item in files:
                output_files = output.setdefault(item.username, [])
                json_data = upload_to_json(item)
                if json_data:
                    output_files.append(json_data)
        else:
            username = identity["username"]
            files = core.Upload.list(DB.session, username)
            output_files = []
            for item in files:
                json_data = upload_to_json(item)
                if json_data:
                    output_files.append(json_data)
            output["self"] = output_files
        return jsonify(output)

    def get(self):
        """
        Retrieve a list of uploads
        """
        if "public" in request.args:
            return self._get_public()
        else:
            return self._get_private()


class Upload(Resource):
    """
    A list of the current user's uploaded files
    """

    FILE_MAPPINGS = {
        "gif": ("gif", "image/gif"),
        "jpg": ("jpeg", "image/jpeg"),
        "jpeg": ("jpeg", "image/jpeg"),
        "png": ("png", "image/png"),
    }

    def _rotated(self, fullname):
        im = Image.open(fullname)
        o_id = {v: k for k, v in EXIF_TAGS.items()}["Orientation"]
        orientation = im.getexif().get(o_id)
        if not orientation:
            return im
        if orientation == 3:
            im = im.rotate(180, expand=True)
        elif orientation == 6:
            im = im.rotate(270, expand=True)
        elif orientation == 8:
            im = im.rotate(90, expand=True)
        return im

    def _thumbnail(self, fullname, size):
        from io import BytesIO

        im = self._rotated(fullname)

        # Limit the size to an upper-bound. This prevents users from enlarging
        # files to inhumane sizes triggering a DoS
        if size and size < 4000:
            im.thumbnail((size, size))

        _, extension = fullname.rsplit(".", 1)
        pillow_type, mediatype = Upload.FILE_MAPPINGS[extension.lower()]
        output = BytesIO()
        im.save(output, format=pillow_type)
        return output, mediatype

    def get(self, uuid):
        """
        Retrieve a single file
        """
        app = cast("MyFlask", current_app)
        data_folder = app.localconfig.get(
            "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
        )
        db_instance = (
            DB.session.query(DBUpload).filter_by(uuid=uuid).one_or_none()
        )
        if not db_instance:
            return "File not found", 404

        size = request.args.get("size", 0, type=int)
        fullname = join(data_folder, db_instance.filename)
        thumbnail, mediatype = self._thumbnail(fullname, size)
        output = make_response(thumbnail.getvalue())
        output.headers["Content-Type"] = mediatype
        output.headers.set(
            "Content-Disposition",
            "inline",
            filename="thn_%s" % (basename(db_instance.filename)),
        )
        return output

    def delete(self, uuid):
        """
        Retrieve a single file
        """
        db_instance = (
            DB.session.query(DBUpload).filter_by(uuid=uuid).one_or_none()
        )
        if not db_instance:
            return "File not found", 404
        identity, all_permissions = get_user_permissions(request)
        if (
            "admin_files" not in all_permissions
            and identity["username"] != db_instance.username
        ):
            return "Access Denied", 403
        app = cast("MyFlask", current_app)
        data_folder = app.localconfig.get(
            "app", "upload_folder", fallback=core.Upload.FALLBACK_FOLDER
        )
        fullname = join(data_folder, db_instance.filename)
        unlink(fullname)
        DB.session.delete(db_instance)
        DB.session.commit()
        app = cast("MyFlask", current_app)
        app.pusher.send_file_event("file-deleted", {"id": uuid})
        return "OK"


class AuditLog(Resource):
    """
    A list of audit-messages
    """

    @require_permissions("view_audit_log")
    def get(self):
        query = DB.session.query(DBAuditLog).order_by(
            DBAuditLog.timestamp.desc()  # type: ignore
        )
        output = []
        for row in query:
            output.append(
                {
                    "timestamp": row.timestamp.isoformat(),
                    "username": row.username,
                    "type": row.type_,
                    "message": row.message,
                }
            )
        return output


class Job(Resource):
    def _action_advance(self, station_name, team_name):
        auth, permissions = get_user_permissions(request)

        app = cast("MyFlask", current_app)
        pusher_channel = app.localconfig.get(
            "pusher_channels",
            "team_station_state",
            fallback="team_station_state_dev",
        )

        if "admin_stations" in permissions or (
            "manage_station" in permissions
            and core.User.may_access_station(
                DB.session, auth["username"], station_name
            )
        ):
            new_state = core.Team.advance_on_station(
                DB.session, team_name, station_name
            )
            output = {"result": {"state": new_state.value}}
            app.pusher.send_team_event(
                "state-change",
                {
                    "station": station_name,
                    "team": team_name,
                    "new_state": new_state.value,
                },
            )
            return output, 200
        else:
            return "Access denied to this station!", 401

    def _action_set_score(self, station_name, team_name, score):
        score = validate_score(score)
        auth, permissions = get_user_permissions(request)

        app = cast("MyFlask", current_app)
        pusher_channel = app.localconfig.get(
            "pusher_channels",
            "team_station_state",
            fallback="team_station_state_dev",
        )

        if "admin_stations" in permissions or (
            "manage_station" in permissions
            and core.User.may_access_station(
                DB.session, auth["username"], station_name
            )
        ):
            LOG.info(
                "Setting score of %s on %s to %s (by user: %s)",
                team_name,
                station_name,
                score,
                auth["username"],
            )
            old_score, new_score = core.Team.set_station_score(
                DB.session, team_name, station_name, score
            )
            if old_score != new_score:
                core.add_audit_log(
                    DB.session,
                    auth["username"],
                    AuditType.STATION_SCORE,
                    "Change score of team %r from %s to %s on station %s"
                    % (team_name, old_score, score, station_name),
                )
            output = {
                "new_score": new_score,
            }
            app.pusher.send_team_event(
                "score-change",
                {
                    "station": station_name,
                    "team": team_name,
                    "new_score": new_score,
                },
            )
            return output, 200
        else:
            return "Access denied to this station!", 401

    def _action_set_questionnaire_score(self, station_name, team_name, score):
        auth, permissions = get_user_permissions(request)
        score = validate_score(score)

        app = cast("MyFlask", current_app)
        pusher_channel = app.localconfig.get(
            "pusher_channels",
            "team_station_state",
            fallback="team_station_state_dev",
        )

        if "admin_stations" in permissions or (
            "manage_station" in permissions
            and core.User.may_access_station(
                DB.session, auth["username"], station_name
            )
        ):
            LOG.info(
                "Setting questionnaire score of %s on %s to %s ("
                "by user: %s)",
                team_name,
                station_name,
                score,
                auth["username"],
            )
            try:
                app = cast("MyFlask", current_app)
                old_score, new_score = core.set_questionnaire_score(
                    app.localconfig,
                    DB.session,
                    team_name,
                    station_name,
                    score,
                )
            except NoQuestionnaireForStation:
                LOG.error(
                    "No questionnaire assigned to station %r!",
                    station_name,
                )
                return (
                    "No questionnaire assigned to station %r!" % station_name,
                    500,
                )
            if old_score != new_score:
                core.add_audit_log(
                    DB.session,
                    auth["username"],
                    AuditType.QUESTIONNAIRE_SCORE,
                    "Change questionnaire score of team %r from %s to %s on station %s"
                    % (team_name, old_score, score, station_name),
                )
            output = {
                "new_score": new_score,
            }
            app.pusher.send_team_event(
                "questionnaire-score-change",
                {
                    "stationName": station_name,
                    "teamName": team_name,
                    "score": new_score,
                },
            )
            return output, 200
        else:
            return "Access denied to this station!", 401

    @require_permissions("manage_station")
    def post(self):
        data = request.get_json()
        parsed_data = JobSchema.model_validate(data)
        action = parsed_data.action
        func = getattr(self, "_action_%s" % action, None)
        if not func:
            LOG.debug("Unknown job %r requested!", parsed_data.action)
            return "%r is an unknown job action" % action, 400
        return func(**parsed_data.args)
