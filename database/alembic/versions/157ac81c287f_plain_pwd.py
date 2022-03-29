"""plain_pwd

Revision ID: 157ac81c287f
Revises: 446941ff9160
Create Date: 2017-07-02 17:16:13.002523

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "157ac81c287f"
down_revision = "446941ff9160"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "password_is_plaintext",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
    )


def downgrade():
    op.drop_column("user", "password_is_plaintext")
