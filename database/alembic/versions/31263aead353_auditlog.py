"""auditlog

Revision ID: 31263aead353
Revises: aa646c7ee31e
Create Date: 2019-05-10 10:33:11.736984

"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '31263aead353'
down_revision = 'aa646c7ee31e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'auditlog',
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            default=datetime.now(timezone.utc),
            server_default=sa.text("(now() at time zone 'utc')")
        ),
        sa.Column(
            'user', sa.Unicode,
            sa.ForeignKey('user.name', onupdate='CASCADE', ondelete='SET NULL'),
        ),
        sa.Column('type', sa.Unicode, nullable=False),
        sa.Column('message', sa.Unicode, nullable=False),
    )


def downgrade():
    op.drop_table('auditlog')
