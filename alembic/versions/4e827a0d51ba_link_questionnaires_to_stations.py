"""link-questionnaires-to-stations

Revision ID: 4e827a0d51ba
Revises: 5753565874d5
Create Date: 2025-04-06 10:18:03.051354

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4e827a0d51ba"
down_revision = "5753565874d5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "questionnaire",
        sa.Column("station_name", sa.Unicode(), nullable=True),
    )
    op.create_foreign_key(
        "for_station",
        "questionnaire",
        "station",
        ["station_name"],
        ["name"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("for_station", "questionnaire", type_="foreignkey")
    op.drop_column("questionnaire", "station_name")
