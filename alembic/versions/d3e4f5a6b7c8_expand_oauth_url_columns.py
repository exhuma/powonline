"""expand-oauth-url-columns

Increase profile_url and image_url in oauth_connection to unbounded Unicode
(TEXT) to accommodate OAuth providers that return URLs longer than 512 chars.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-05-13 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "oauth_connection",
        "profile_url",
        type_=sa.Unicode(2048),
        existing_type=sa.Unicode(512),
    )
    op.alter_column(
        "oauth_connection",
        "image_url",
        type_=sa.Unicode(2048),
        existing_type=sa.Unicode(512),
    )


def downgrade() -> None:
    op.alter_column(
        "oauth_connection",
        "image_url",
        type_=sa.Unicode(512),
        existing_type=sa.Unicode(2048),
    )
    op.alter_column(
        "oauth_connection",
        "profile_url",
        type_=sa.Unicode(512),
        existing_type=sa.Unicode(2048),
    )
