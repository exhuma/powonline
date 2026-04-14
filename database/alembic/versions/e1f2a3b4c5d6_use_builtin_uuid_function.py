"""use-builtin-uuid-function

This migration replaces the uuid-ossp extension dependency with PostgreSQL's
built-in gen_random_uuid() function (available in PG 13+), allowing the use
of vanilla PostgreSQL images without custom extensions.

Revision ID: e1f2a3b4c5d6
Revises: 4e827a0d51ba
Create Date: 2026-04-14 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "4e827a0d51ba"
branch_labels = None
depends_on = None


def upgrade():
    # Alter the existing uploads.id column to use the built-in gen_random_uuid()
    # instead of uuid_generate_v4() from the uuid-ossp extension
    op.alter_column(
        "uploads",
        "id",
        existing_type=sa.dialects.postgresql.UUID(),
        server_default=sa.func.gen_random_uuid(),
    )


def downgrade():
    # Downgrade back to using uuid_generate_v4() from the extension
    op.alter_column(
        "uploads",
        "id",
        existing_type=sa.dialects.postgresql.UUID(),
        server_default=sa.func.uuid_generate_v4(),
    )
