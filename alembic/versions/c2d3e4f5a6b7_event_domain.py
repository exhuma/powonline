"""add event_domain table

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5g6
Create Date: 2026-04-16 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5g6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_domain",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.Unicode(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name="event_domain_event_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index("ix_event_domain_event_id", "event_domain", ["event_id"])


def downgrade():
    op.drop_index("ix_event_domain_event_id", table_name="event_domain")
    op.drop_table("event_domain")
