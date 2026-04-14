"""staff_role

Revision ID: 054abcb75e0e
Revises: 31263aead353
Create Date: 2019-05-10 12:13:27.647576

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "054abcb75e0e"
down_revision = "31263aead353"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("INSERT INTO role VALUES ('staff')")


def downgrade():
    op.execute("DELETE FROM role WHERE name='staff'")
