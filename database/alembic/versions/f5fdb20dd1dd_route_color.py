"""route-color

Revision ID: f5fdb20dd1dd
Revises: 157ac81c287f
Create Date: 2018-02-26 12:44:11.341006

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f5fdb20dd1dd'
down_revision = '157ac81c287f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('route', sa.Column('color', sa.Unicode()))


def downgrade():
    op.drop_column('route', 'color')
