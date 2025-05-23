import logging
from codecs import encode
from datetime import datetime, timezone
from enum import Enum
from os import environ, urandom
from typing import Any
from urllib.parse import urlparse, urlunparse

import sqlalchemy.types as types
from bcrypt import checkpw, gensalt, hashpw
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    FetchedValue,
    ForeignKey,
    Integer,
    Table,
    Unicode,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import BYTEA, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session

LOG = logging.getLogger(__name__)
DB = SQLAlchemy()


def get_dsn():
    dsn = environ.get("POWONLINE_DSN", "").strip()
    if dsn:
        parsed = urlparse(dsn)
        if parsed.scheme == "postgresql":
            dsn = urlunparse(parsed._replace(scheme="postgresql+psycopg"))
    return dsn


class AuditType(Enum):
    ADMIN = "admin"
    QUESTIONNAIRE_SCORE = "questionnaire_score"
    STATION_SCORE = "station_score"


class TeamState(Enum):
    UNKNOWN = "unknown"
    ARRIVED = "arrived"
    FINISHED = "finished"
    UNREACHABLE = "unreachable"


class TimestampMixin:
    inserted = Column(
        DateTime(timezone=True),
        FetchedValue(),
        nullable=False,
        server_default=func.now(),
    )
    updated = Column(DateTime(timezone=True), nullable=True)


class TeamStateType(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return value.value

    def process_result_value(self, value, dialect):
        return TeamState(value)


class Setting(DB.Model):  # type: ignore
    __tablename__ = "setting"

    key = Column(Unicode, primary_key=True, nullable=False)
    value = Column(Unicode)
    description = Column(Unicode)


class Message(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    content = Column(Unicode)
    user = Column(
        Unicode,
        ForeignKey(
            "user.name",
            name="message_user_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )
    team = Column(
        Unicode,
        ForeignKey(
            "team.name",
            name="message_team_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )


class Team(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "team"
    __table_args__ = (
        UniqueConstraint("confirmation_key", name="team_confirmation_key"),
    )

    name: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column()
    order: Mapped[int] = mapped_column(server_default="500")
    cancelled: Mapped[bool] = mapped_column(server_default="false")
    contact: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    comments: Mapped[str | None] = mapped_column()
    is_confirmed: Mapped[bool] = mapped_column(server_default="false")
    confirmation_key: Mapped[str] = mapped_column(server_default="")
    accepted: Mapped[bool] = mapped_column(server_default="false")
    completed: Mapped[bool] = mapped_column(server_default="false")
    num_vegetarians: Mapped[int | None] = mapped_column()
    num_participants: Mapped[int | None] = mapped_column()
    planned_start_time: Mapped[datetime | None] = mapped_column()
    effective_start_time: Mapped[datetime | None] = mapped_column()
    finish_time: Mapped[datetime | None] = mapped_column()
    route_name: Mapped[str | None] = mapped_column(
        ForeignKey("route.name", onupdate="CASCADE", ondelete="SET NULL")
    )
    owner = Column(
        Unicode,
        ForeignKey(
            "user.name",
            name="team_owner_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )
    owner_user = relationship("User")

    route: Mapped["Route"] = relationship("Route", back_populates="teams")
    stations: Mapped[list["Station"]] = relationship(
        "Station", secondary="team_station_state", viewonly=True
    )
    station_states: Mapped[list["TeamStation"]] = relationship(
        "TeamStation", viewonly=True
    )
    questionnaire_scores: Mapped[list["TeamQuestionnaire"]] = relationship(
        "TeamQuestionnaire", viewonly=True
    )
    questionnaires: Mapped[list["Questionnaire"]] = relationship(
        "Questionnaire", secondary="questionnaire_score", viewonly=True
    )

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def reset_confirmation_key(self) -> None:
        randbytes = encode(urandom(100), "hex")[:30]
        self.confirmation_key = randbytes.decode("ascii")

    def __repr__(self) -> str:
        return "Team(name=%r)" % self.name


class Station(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "station"
    name: Mapped[str] = mapped_column(primary_key=True)
    contact: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    order: Mapped[int] = mapped_column(server_default="500")
    is_start: Mapped[bool] = mapped_column(server_default="false")
    is_end: Mapped[bool] = mapped_column(server_default="false")

    routes: Mapped[set["Route"]] = relationship(
        "Route",
        secondary="route_station",
        back_populates="stations",
        collection_class=set,
    )

    users: Mapped[set["User"]] = relationship(
        "User",
        secondary="user_station",
        back_populates="stations",
        collection_class=set,
    )

    teams: Mapped[list["Team"]] = relationship(
        "Team", secondary="team_station_state", viewonly=True
    )
    states: Mapped[list["TeamStation"]] = relationship(
        "TeamStation", back_populates="station"
    )

    questionnaires = relationship("Questionnaire", back_populates="station")

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return "Station(name=%r)" % self.name


class Route(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "route"

    name: Mapped[str] = mapped_column(primary_key=True)
    color: Mapped[str | None] = mapped_column()
    teams: Mapped[set["Team"]] = relationship(
        "Team", back_populates="route", collection_class=set
    )
    stations: Mapped[set["Station"]] = relationship(
        "Station",
        secondary="route_station",
        back_populates="routes",
        collection_class=set,
    )

    def __repr__(self) -> str:
        return "Route(name=%r)" % self.name

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class OauthConnection(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "oauth_connection"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_: Mapped[str | None] = mapped_column(
        ForeignKey(
            "user.name",
            name="oauth_connection_user_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        name="user",
    )
    provider_id: Mapped[str | None] = mapped_column(Unicode(255))
    provider_user_id: Mapped[str | None] = mapped_column(Unicode(255))
    access_token: Mapped[str | None] = mapped_column(Unicode(255))
    secret: Mapped[str | None] = mapped_column(Unicode(255))
    display_name: Mapped[str | None] = mapped_column(Unicode(255))
    profile_url: Mapped[str | None] = mapped_column(Unicode(512))
    image_url: Mapped[str | None] = mapped_column(Unicode(512))
    rank: Mapped[int | None] = mapped_column()

    user: Mapped["User"] = relationship(
        "User", back_populates="oauth_connection"
    )


class User(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("email", name="user_email_key"),)

    name: Mapped[str] = mapped_column(primary_key=True)
    password: Mapped[bytes | None] = mapped_column(BYTEA)
    password_is_plaintext: Mapped[bool] = mapped_column(
        nullable=False, server_default="false"
    )
    email: Mapped[str | None] = mapped_column()
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locale: Mapped[str] = mapped_column(Unicode(2))

    oauth_connection: Mapped[list["OauthConnection"]] = relationship(
        "OauthConnection", back_populates="user"
    )
    stations: Mapped[set["Station"]] = relationship(
        "User",
        secondary="user_station",
        back_populates="users",
        collection_class=set,
    )
    files: Mapped[list["Upload"]] = relationship(
        "Upload", back_populates="user"
    )
    auditlog: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )

    @property
    def avatar_url(self) -> str:
        if not self.oauth_connection:
            return ""
        try:
            if not self.oauth_connection[0].image_url:
                return ""
            return self.oauth_connection[0].image_url
        except IndexError:
            LOG.debug(
                "Unexpected error occurred with the avatar-url", exc_info=True
            )
            return ""

    @staticmethod
    def get_or_create(session: scoped_session, username: str) -> "User":
        """
        Returns a user instance by name. Creates it if missing.
        """
        query = session.query(User).filter_by(name=username)
        instance = query.one_or_none()
        if not instance:
            randbytes = encode(urandom(100), "hex")[:30]
            password = randbytes.decode("ascii")
            instance = User(username, password)
            session.add(instance)
            LOG.warning("User initialised with random password!")
        return instance

    def __init__(self, name: str, password: str) -> None:
        self.name = name
        self.password = hashpw(password.encode("utf8"), gensalt())
        self.password_is_plaintext = False

    def checkpw(self, password: str) -> bool:
        if self.password_is_plaintext:
            self.password = hashpw(password.encode("utf8"), gensalt())
            self.password_is_plaintext = False
        return checkpw(password.encode("utf8"), self.password or b"")

    def setpw(self, new_password: str) -> None:
        self.password = hashpw(new_password.encode("utf8"), gensalt())
        self.password_is_plaintext = False

    roles: Mapped[set["Role"]] = relationship(
        "Role",
        secondary="user_role",
        back_populates="users",
        collection_class=set,
    )
    stations: Mapped[set["Station"]] = relationship(
        "Station",
        secondary="user_station",
        back_populates="users",
        collection_class=set,
    )


class Role(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "role"
    name: Mapped[str] = mapped_column(primary_key=True)
    users: Mapped[set["User"]] = relationship(
        "User",
        secondary="user_role",
        back_populates="roles",
        collection_class=set,
    )

    def __init__(self) -> None:
        self.name = "Example Station"

    @staticmethod
    def get_or_create(session: scoped_session, name: str) -> "Role":
        """
        Retrieves a role with name *name*.

        If it does not exist yet in the DB it will be created.
        """
        query = session.query(Role).filter_by(name=name)
        existing = query.one_or_none()
        if not existing:
            output = Role()  # type: ignore
            output.name = name
            session.add(output)
        else:
            output = existing
        return output  # type: ignore


class TeamStation(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "team_station_state"

    team_name: Mapped[str] = mapped_column(
        ForeignKey("team.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    station_name: Mapped[str] = mapped_column(
        ForeignKey("station.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    state: Mapped[TeamStateType | None] = mapped_column(
        TeamStateType, default=TeamState.UNKNOWN
    )
    score: Mapped[int | None] = mapped_column(nullable=True, default=None)
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(),
        server_default=func.now(),
    )

    team: Mapped["Team"] = relationship("Team")
    station: Mapped["Station"] = relationship(
        "Station", back_populates="states"
    )

    def __init__(
        self,
        team_name: str,
        station_name: str,
        state: TeamState = TeamState.UNKNOWN,
    ) -> None:
        self.team_name = team_name
        self.station_name = station_name
        self.state = state


class Questionnaire(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "questionnaire"

    name: Mapped[str] = mapped_column(nullable=False, primary_key=True)
    max_score: Mapped[int | None] = mapped_column()
    order: Mapped[int | None] = mapped_column(server_default="0")
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(),
        server_default=func.now(),
    )
    station_name: Mapped[str] = mapped_column(
        Unicode,
        ForeignKey(
            "station.name",
            name="for_station",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    teams: Mapped[set["Team"]] = relationship(
        "Team", secondary="questionnaire_score", viewonly=True
    )  # uses an AssociationObject
    station = relationship("Station")

    def __init__(
        self,
        name: str,
        max_score: int,
        order: int = 0,
        station_name: str | None = None,
        inserted: datetime | None = None,
        updated: datetime | None = None,
    ):
        self.name = name
        self.max_score = max_score
        self.order = order
        self.station_name = station_name or None
        if updated:
            self.updated = updated
        if inserted:
            LOG.debug("Ignoring 'inserted' timestamp (%s)", inserted)


class TeamQuestionnaire(DB.Model, TimestampMixin):  # type: ignore
    __tablename__ = "questionnaire_score"

    team_name: Mapped[str] = mapped_column(
        ForeignKey("team.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
        name="team",
    )
    questionnaire_name: Mapped[str] = mapped_column(
        ForeignKey(
            "questionnaire.name", onupdate="CASCADE", ondelete="CASCADE"
        ),
        primary_key=True,
        name="questionnaire",
    )
    score: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(),
        server_default=func.now(),
    )

    team: Mapped["Team"] = relationship("Team")
    questionnaire: Mapped["Questionnaire"] = relationship("Questionnaire")

    def __init__(
        self, team_name: str, questionnaire_name: str, score: int = 0
    ) -> None:
        self.team_name = team_name
        self.questionnaire_name = questionnaire_name
        self.score = score


class Upload(DB.Model):  # type: ignore
    __tablename__ = "uploads"
    filename: Mapped[str] = mapped_column(Unicode, primary_key=True)
    username: Mapped[str] = mapped_column(
        Unicode(50),
        ForeignKey("user.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    uuid: Mapped[UUID] = mapped_column(
        UUID,
        unique=True,
        nullable=False,
        name="id",
        server_default=func.uuid_generate_v4(),
    )

    user: Mapped["User"] = relationship("User", back_populates="files")

    def __init__(self, relname: str, username: str) -> None:
        self.filename = relname
        self.username = username

    @staticmethod
    def get_or_create(
        session: scoped_session, relname: str, username: str
    ) -> "Upload":
        """
        Returns an upload entity. Create it if it is missing
        """
        query = session.query(Upload).filter_by(
            filename=relname, username=username
        )
        instance = query.one_or_none()
        if not instance:
            instance = Upload(relname, username)
            session.add(instance)
            LOG.debug("New file added to DB")
        else:
            LOG.debug("Using existing DB entry")
        return instance


class AuditLog(DB.Model):  # type: ignore
    __tablename__ = "auditlog"
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(timezone.utc),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        ForeignKey("user.name", onupdate="CASCADE", ondelete="SET NULL"),
        name="user",
        primary_key=True,
        nullable=True,
    )
    type_: Mapped[str] = mapped_column(name="type", nullable=False)
    message: Mapped[str] = mapped_column(name="message", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="auditlog")

    def __init__(
        self, timestamp: datetime, username: str, type_: AuditType, message: str
    ) -> None:
        self.timestamp = timestamp
        self.username = username
        self.type_ = type_.value
        self.message = message


route_station_table = Table(
    "route_station",
    DB.metadata,
    Column(
        "route_name",
        Unicode,
        ForeignKey("route.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "station_name",
        Unicode,
        ForeignKey("station.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("score", Integer),
    Column(
        "inserted",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    Column("updated", DateTime(timezone=True), server_default="null"),
)

user_station_table = Table(
    "user_station",
    DB.metadata,
    Column(
        "user_name",
        Unicode,
        ForeignKey("user.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "station_name",
        Unicode,
        ForeignKey("station.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("inserted", DateTime(timezone=True), server_default=func.now()),
    Column("updated", DateTime(timezone=True), server_default="null"),
)

user_role_table = Table(
    "user_role",
    DB.metadata,
    Column(
        "user_name",
        Unicode,
        ForeignKey("user.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_name",
        Unicode,
        ForeignKey("role.name", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("inserted", DateTime(timezone=True), server_default=func.now()),
    Column("updated", DateTime(timezone=True), server_default="null"),
)


class Job:
    def __init__(self):
        self.action = "example_action"
        self.args = {}
