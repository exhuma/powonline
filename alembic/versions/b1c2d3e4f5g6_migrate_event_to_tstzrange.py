"""migrate-event-to-tstzrange

Revision ID: b1c2d3e4f5g6
Revises: 9f3c2a7d8b1e
Create Date: 2026-04-14 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5g6"
down_revision = "9f3c2a7d8b1e"
branch_labels = None
depends_on = None


def upgrade():
    # Add the new time_range column with a default value for existing rows
    # Using a temporary default that will be updated based on existing start_time/end_time
    op.add_column(
        "event",
        sa.Column(
            "time_range",
            postgresql.TSTZRANGE(),
            nullable=True,  # Temporarily nullable to handle existing rows
        ),
    )

    # Update existing rows: convert start_time and end_time to time_range
    # Use raw SQL to handle the conversion with PostgreSQL's tstzrange function
    # tstzrange is used for timezone-aware timestamps
    op.execute("""
    UPDATE event
    SET time_range = tstzrange(
        start_time,
        end_time,
        '[)'
    )
    WHERE start_time IS NOT NULL AND end_time IS NOT NULL
    """)

    # Now make time_range non-nullable
    op.alter_column("event", "time_range", nullable=False)

    # Drop the old columns
    op.drop_column("event", "start_time")
    op.drop_column("event", "end_time")


def downgrade():
    # Add back the old columns
    op.add_column(
        "event",
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "event",
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
    )

    # Convert time_range back to start_time and end_time
    op.execute("""
    UPDATE event
    SET start_time = lower(time_range),
        end_time = upper(time_range)
    WHERE time_range IS NOT NULL
    """)

    # Drop the time_range column
    op.drop_column("event", "time_range")
