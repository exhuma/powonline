"""auth

Revision ID: adc36a2767ab
Revises: 6515a04b94bf
Create Date: 2017-06-30 19:27:34.113674

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import BYTEA

# revision identifiers, used by Alembic.
revision = 'adc36a2767ab'
down_revision = '6515a04b94bf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('password', BYTEA, nullable=False))


def downgrade():
    op.drop_column('user', 'password')
