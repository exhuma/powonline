"""initial

Revision ID: 3ee5e487c3e5
Revises:
Create Date: 2017-06-19 08:07:51.151982

"""
from datetime import datetime

from alembic import op
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
    func,
)

# revision identifiers, used by Alembic.
revision = "3ee5e487c3e5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "route",
        Column("name", Unicode, primary_key=True),
    )

    op.create_table(
        "team",
        Column("name", Unicode, primary_key=True, nullable=False),
        Column("email", Unicode, nullable=False),
        Column("order", Integer, nullable=False, server_default="500"),
        Column("cancelled", Boolean, nullable=False, server_default="false"),
        Column("contact", Unicode),
        Column("phone", Unicode),
        Column("comments", Unicode),
        Column("is_confirmed", Boolean, nullable=False, server_default="false"),
        Column("confirmation_key", Unicode, nullable=False, server_default=""),
        Column("accepted", Boolean, nullable=False, server_default="false"),
        Column("completed", Boolean, nullable=False, server_default="false"),
        Column("inserted", DateTime, nullable=False, server_default=func.now()),
        Column("updated", DateTime, nullable=False, server_default=func.now()),
        Column("num_vegetarians", Integer),
        Column("num_participants", Integer),
        Column("planned_start_time", DateTime),
        Column("effective_start_time", DateTime),
        Column("finish_time", DateTime),
        Column(
            "route_name",
            Unicode,
            ForeignKey("route.name", onupdate="CASCADE", ondelete="SET NULL"),
        ),
    )

    op.create_table(
        "station",
        Column("name", Unicode, primary_key=True, nullable=False),
        Column("contact", Unicode),
        Column("phone", Unicode),
        Column("is_start", Boolean, nullable=False, server_default="false"),
        Column("is_end", Boolean, nullable=False, server_default="false"),
    )

    op.create_table("user", Column("name", Unicode, primary_key=True))

    op.create_table(
        "role",
        Column("name", Unicode, primary_key=True),
    )

    op.create_table(
        "team_station_state",
        Column(
            "team_name",
            Unicode,
            ForeignKey("team.name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column(
            "station_name",
            Unicode,
            ForeignKey("station.name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column("state", Unicode, default="unknown"),
        Column("score", Integer, nullable=True, default=None),
        Column(
            "updated",
            DateTime(timezone=True),
            nullable=False,
            default=datetime.now(),
            server_default=func.now(),
        ),
    )

    op.create_table(
        "route_station",
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
        Column("score", Integer, nullable=True, default=None),
        Column(
            "updated",
            DateTime(timezone=True),
            nullable=False,
            default=datetime.now(),
            server_default=func.now(),
        ),
    )

    op.create_table(
        "user_station",
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
    )

    op.create_table(
        "user_role",
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
    )


def downgrade():
    op.drop_table("user_role")
    op.drop_table("user_station")
    op.drop_table("route_station")
    op.drop_table("team_station_state")
    op.drop_table("role")
    op.drop_table("user")
    op.drop_table("station")
    op.drop_table("team")
    op.drop_table("route")
