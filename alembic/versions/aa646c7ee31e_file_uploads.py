"""file-uploads

Revision ID: aa646c7ee31e
Revises: 5be3d628dcc3
Create Date: 2019-05-05 11:56:21.910210

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "aa646c7ee31e"
down_revision = "5be3d628dcc3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "uploads",
        sa.Column("filename", sa.Unicode, primary_key=True),
        sa.Column(
            "username",
            sa.String(50),
            sa.ForeignKey("user.name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "id",
            UUID,
            unique=True,
            nullable=False,
            server_default=sa.func.uuid_generate_v4(),
        ),
    )


def downgrade():
    op.drop_table("uploads")
