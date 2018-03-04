"""default_roles

Revision ID: 446941ff9160
Revises: adc36a2767ab
Create Date: 2017-06-30 20:24:18.115522

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '446941ff9160'
down_revision = 'adc36a2767ab'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("INSERT INTO role VALUES ('admin'), ('station_manager')")


def downgrade():
    op.execute('DELETE FROM role')
