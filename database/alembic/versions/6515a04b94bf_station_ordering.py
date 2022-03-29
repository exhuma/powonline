"""station-ordering

Revision ID: 6515a04b94bf
Revises: 3ee5e487c3e5
Create Date: 2017-06-26 21:19:37.725922

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '6515a04b94bf'
down_revision = '3ee5e487c3e5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('station', sa.Column(
        'order', sa.Integer, server_default='500'))


def downgrade():
    op.drop_column('station', 'order')
