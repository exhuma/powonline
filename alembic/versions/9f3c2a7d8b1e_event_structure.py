"""event-structure

Revision ID: 9f3c2a7d8b1e
Revises: e1f2a3b4c5d6
Create Date: 2026-04-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f3c2a7d8b1e"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "inserted",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "event_user_role",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_name", sa.Unicode(), nullable=False),
        sa.Column("role_name", sa.Unicode(), nullable=False),
        sa.Column(
            "inserted",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_name"],
            ["user.name"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("event_id", "user_name", "role_name"),
    )

    op.add_column(
        "route",
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("event.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "team",
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("event.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "station",
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("event.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "questionnaire",
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("event.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "uploads",
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("event.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "auditlog",
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("event.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    op.create_index("ix_route_event_id", "route", ["event_id"])
    op.create_index("ix_team_event_id", "team", ["event_id"])
    op.create_index("ix_station_event_id", "station", ["event_id"])
    op.create_index("ix_questionnaire_event_id", "questionnaire", ["event_id"])
    op.create_index("ix_uploads_event_id", "uploads", ["event_id"])
    op.create_index("ix_auditlog_event_id", "auditlog", ["event_id"])


def downgrade():
    op.drop_index("ix_auditlog_event_id", table_name="auditlog")
    op.drop_index("ix_uploads_event_id", table_name="uploads")
    op.drop_index("ix_questionnaire_event_id", table_name="questionnaire")
    op.drop_index("ix_station_event_id", table_name="station")
    op.drop_index("ix_team_event_id", table_name="team")
    op.drop_index("ix_route_event_id", table_name="route")

    op.drop_column("auditlog", "event_id")
    op.drop_column("uploads", "event_id")
    op.drop_column("questionnaire", "event_id")
    op.drop_column("station", "event_id")
    op.drop_column("team", "event_id")
    op.drop_column("route", "event_id")

    op.drop_table("event_user_role")
    op.drop_table("event")
