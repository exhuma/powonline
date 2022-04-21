"""lost-tracker-alignment

Revision ID: 5be3d628dcc3
Revises: f5fdb20dd1dd
Create Date: 2018-03-12 08:06:16.806938

Create elements in the database which make the DB more similar to the old
lost-tracker DB, making data-migration easier.
"""

from textwrap import dedent

from alembic import op
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
)

# revision identifiers, used by Alembic.
revision = "5be3d628dcc3"
down_revision = "f5fdb20dd1dd"
branch_labels = None
depends_on = None


def create_updated_trigger(tablename):
    op.execute(
        dedent(
            """\
        CREATE TRIGGER {0}_updated_timestamp
        BEFORE UPDATE ON public."{0}"
        FOR ROW WHEN ((old.* IS DISTINCT FROM new.*))

        EXECUTE PROCEDURE public.set_updated_column();"""
        ).format(tablename)
    )


def add_ts(tablename, ins=True, upd=True):
    if ins:
        op.execute(
            'ALTER TABLE "{}" ADD inserted '
            "TIMESTAMP WITH TIME ZONE DEFAULT NOW()".format(tablename)
        )
    if upd:
        op.execute(
            (
                'ALTER TABLE "{}" ADD updated '
                "TIMESTAMP WITH TIME ZONE DEFAULT NULL".format(tablename)
            )
        )


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog")
    op.execute(
        dedent(
            """\
        CREATE FUNCTION public.set_updated_column() RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                NEW.updated = NOW();
                RETURN NEW;
            END;
            $$;
        """
        )
    )

    add_ts("role")
    add_ts("route")
    add_ts("station")
    add_ts("user")
    add_ts("user_role")
    add_ts("user_station")
    add_ts("route_station", upd=False)
    add_ts("team_station_state", upd=False)

    op.add_column("user", Column("email", Unicode, unique=True))
    op.add_column("user", Column("locale", String(2)))
    op.add_column(
        "user", Column("active", Boolean, nullable=False, server_default="true")
    )
    op.add_column("user", Column("confirmed_at", DateTime(timezone=True)))
    op.add_column(
        "team",
        Column(
            "owner",
            Unicode(),
            ForeignKey("user.name", onupdate="CASCADE", ondelete="CASCADE"),
        ),
    )

    create_updated_trigger("team")
    create_updated_trigger("role")
    create_updated_trigger("route")
    create_updated_trigger("station")
    create_updated_trigger("user")
    create_updated_trigger("user_role")
    create_updated_trigger("user_station")
    create_updated_trigger("route_station")
    create_updated_trigger("team_station_state")

    op.create_table(
        "oauth_connection",
        Column("id", Integer, primary_key=True, nullable=False),
        Column(
            "user",
            Unicode,
            ForeignKey("user.name", ondelete="CASCADE", onupdate="CASCADE"),
        ),
        Column("provider_id", String(255)),
        Column("provider_user_id", String(255)),
        Column("access_token", String(255)),
        Column("secret", String(255)),
        Column("display_name", Unicode(255)),
        Column("profile_url", Unicode(512)),
        Column("image_url", Unicode(512)),
        Column("rank", Integer),
    )
    add_ts("oauth_connection")
    create_updated_trigger("oauth_connection")

    op.create_table(
        "questionnaire",
        Column("name", Unicode(), primary_key=True),
        Column("max_score", Integer),
        Column("order", Integer, nullable=False, server_default="0"),
    )
    add_ts("questionnaire")
    create_updated_trigger("questionnaire")

    op.create_table(
        "questionnaire_score",
        Column(
            "team",
            Unicode,
            ForeignKey("team.name", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        Column(
            "questionnaire",
            Unicode,
            ForeignKey(
                "questionnaire.name", ondelete="CASCADE", onupdate="CASCADE"
            ),
            primary_key=True,
            nullable=False,
        ),
        Column("score", Integer),
    )
    add_ts("questionnaire_score")
    create_updated_trigger("questionnaire_score")

    op.create_table(
        "message",
        Column("id", Integer, primary_key=True),
        Column("content", Unicode),
        Column(
            "user",
            Unicode,
            ForeignKey("user.name", ondelete="CASCADE", onupdate="CASCADE"),
        ),
        Column(
            "team",
            Unicode(),
            ForeignKey("team.name", ondelete="CASCADE", onupdate="CASCADE"),
        ),
    )
    add_ts("message")
    create_updated_trigger("message")

    op.create_table(
        "setting",
        Column("key", String(), primary_key=True),
        Column("value", Unicode),
        Column("description", Unicode),
    )

    op.execute("UPDATE team SET confirmation_key = random()::text")
    op.execute(
        "ALTER TABLE team ADD CONSTRAINT team_confirmation_key "
        "UNIQUE (confirmation_key)"
    )


def downgrade():

    op.execute("ALTER TABLE team DROP CONSTRAINT team_confirmation_key")
    op.drop_constraint("oauth_connection_user_fkey", "oauth_connection")
    op.drop_column("team", "owner")
    op.drop_column("user", "locale")
    op.drop_column("user", "active")
    op.drop_column("user", "confirmed_at")
    op.drop_column("user", "email")

    op.drop_table("setting")
    op.drop_table("message")
    op.drop_table("questionnaire_score")
    op.drop_table("questionnaire")
    op.drop_table("oauth_connection")

    op.execute('DROP TRIGGER role_updated_timestamp ON "role"')
    op.execute("DROP TRIGGER route_updated_timestamp ON route")
    op.execute("DROP TRIGGER station_updated_timestamp ON station")
    op.execute('DROP TRIGGER user_updated_timestamp ON "user"')
    op.execute("DROP TRIGGER user_role_updated_timestamp ON user_role")
    op.execute("DROP TRIGGER user_station_updated_timestamp ON user_station")
    op.execute("DROP TRIGGER route_station_updated_timestamp ON route_station")
    op.execute(
        "DROP TRIGGER "
        "team_station_state_updated_timestamp ON team_station_state"
    )

    op.execute('ALTER TABLE "role" DROP inserted')
    op.execute('ALTER TABLE "role" DROP updated')
    op.execute("ALTER TABLE route DROP inserted")
    op.execute("ALTER TABLE route DROP updated")
    op.execute("ALTER TABLE station DROP inserted")
    op.execute("ALTER TABLE station DROP updated")
    op.execute('ALTER TABLE "user" DROP inserted')
    op.execute('ALTER TABLE "user" DROP updated')
    op.execute("ALTER TABLE user_role DROP inserted")
    op.execute("ALTER TABLE user_role DROP updated")
    op.execute("ALTER TABLE user_station DROP inserted")
    op.execute("ALTER TABLE user_station DROP updated")
    op.execute("ALTER TABLE route_station DROP inserted")
    op.execute("ALTER TABLE team_station_state DROP inserted")
    op.execute("DROP TRIGGER team_updated_timestamp ON team")
    op.execute("DROP FUNCTION set_updated_column")
