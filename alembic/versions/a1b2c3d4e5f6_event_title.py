"""event-title

Revision ID: a1b2c3d4e5f6
Revises: ec1494f947a9
Create Date: 2026-04-26 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "ec1494f947a9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("event", sa.Column("title", sa.Unicode(), nullable=True))


def downgrade():
    op.drop_column("event", "title")
