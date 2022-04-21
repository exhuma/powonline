import argparse
import re
from contextlib import contextmanager
from datetime import date, datetime, time

import psycopg2
from psycopg2.extras import DictCursor

P_TIMESPEC = re.compile(r"^(\d{1,2})[h:](\d{1,2})$")


def convert_start_time(timespec, date_obj):
    """
    Converts a time-string in the form of "19h30" or "19:30" to a time on the
    given *date_obj*.
    """
    if not timespec:
        return None
    match = P_TIMESPEC.match(timespec.strip())
    if not match:
        return None
    hour, minute = match.groups()
    time_obj = time(int(hour, 10), int(minute, 10))
    return datetime.combine(date_obj, time_obj)


@contextmanager
def connect(dsn):
    connection = psycopg2.connect(dsn)
    yield connection
    connection.close()


def add_users(source_db, dest_db):
    print("Migrating users...")
    query = (
        'INSERT INTO "user" '
        "(name, email, password, password_is_plaintext, confirmed_at)"
        " VALUES "
        "(%s, %s, %s, %s, %s) "
        "ON CONFLICT DO NOTHING "
        "RETURNING name, password"
    )
    with source_db.cursor() as source, dest_db.cursor() as dest:
        source.execute('SELECT id, email, confirmed_at FROM "user"')
        for user in source:
            dest.execute(query, (user[1], user[1], "migrator", True, user[2]))
            for row in dest:
                passwd = row[1].tobytes()
                if passwd == b"migrator":
                    pwtype = "default"
                else:
                    pwtype = "custom"
                print("   Created user %s with %s password" % (row[0], pwtype))
    print("done")


def create_routes_from_directions(source_db, dest_db):
    print("Migrating routes...")
    query = (
        'INSERT INTO "route" '
        "(name)"
        " VALUES "
        "(%s) "
        "ON CONFLICT DO NOTHING;"
    )
    with source_db.cursor() as source, dest_db.cursor() as dest:
        source.execute('SELECT DISTINCT direction FROM "group"')
        for direction in source:
            if not direction[0]:
                continue
            dest.execute(query, direction)
            print("   Added route %s" % direction[0])
    print("done")


def migrate_teams(source_db, dest_db):
    print("Migrating teams...")
    source = source_db.cursor(cursor_factory=DictCursor)
    dest = dest_db.cursor(cursor_factory=DictCursor)

    source.execute('SELECT id, email FROM "user"')
    user_map = {user["id"]: user["email"] for user in source}

    source.execute('SELECT * FROM "group"')
    for group in source:
        query = (
            "INSERT INTO team ("
            "name,"
            "email,"
            '"order",'
            "cancelled,"
            "contact,"
            "phone,"
            "comments,"
            "is_confirmed,"
            "confirmation_key,"
            "accepted,"
            "completed,"
            "inserted,"
            "updated,"
            "num_vegetarians,"
            "num_participants,"
            "planned_start_time,"
            "effective_start_time,"
            "finish_time,"
            "route_name,"
            "owner"
            ") VALUES ("
            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"
            ") ON CONFLICT DO NOTHING",
            (
                group["name"],
                group["email"],
                group["order"],
                group["cancelled"],
                group["contact"],
                group["phone"],
                group["comments"],
                group["is_confirmed"],
                group["confirmation_key"],
                group["accepted"],
                group["completed"],
                group["inserted"] or None,
                group["updated"] or None,
                group["num_vegetarians"],
                group["num_participants"],
                convert_start_time(group["start_time"], date(2018, 5, 9)),
                group["departure_time"] or None,
                group["finish_time"] or None,
                group["direction"],
                user_map[group["user_id"]],
            ),
        )
        dest.execute(query[0], query[1])
        print("   Added team %s" % group["name"])
    print("done")


def migrate_stations(source_db, dest_db):
    print("Migrating stations...")
    source = source_db.cursor(cursor_factory=DictCursor)
    dest = dest_db.cursor(cursor_factory=DictCursor)

    source.execute('SELECT * FROM "station"')
    for station in source:
        query = (
            "INSERT INTO station ("
            "name,"
            "contact,"
            "phone,"
            "is_start,"
            "is_end,"
            '"order"'
            ") VALUES ("
            "%s, %s, %s, %s, %s, %s"
            ") ON CONFLICT DO NOTHING",
            (
                station["name"],
                station["contact"],
                station["phone"],
                station["is_start"],
                station["is_end"],
                station["order"],
            ),
        )
        dest.execute(query[0], query[1])
        print("   Added station %s" % station["name"])
    print("done")


def migrate_connections(source_db, dest_db):
    print("Migrating connections...")
    source = source_db.cursor(cursor_factory=DictCursor)
    dest = dest_db.cursor(cursor_factory=DictCursor)

    source.execute('SELECT id, email FROM "user"')
    user_map = {user["id"]: user["email"] for user in source}

    source.execute('SELECT * FROM "connection"')
    for connection in source:
        query = (
            "INSERT INTO oauth_connection ("
            '"user",'
            "provider_id,"
            "provider_user_id,"
            "access_token,"
            "secret,"
            "display_name,"
            "profile_url,"
            "image_url,"
            "rank"
            ") VALUES ("
            "%s, %s, %s, %s, %s, %s, %s, %s, %s"
            ") ON CONFLICT DO NOTHING",
            (
                user_map[connection["user_id"]],
                connection["provider_id"],
                connection["provider_user_id"],
                connection["access_token"],
                connection["secret"],
                connection["display_name"],
                connection["profile_url"],
                connection["image_url"],
                connection["rank"],
            ),
        )
        dest.execute(query[0], query[1])
        print(
            "   Added oauth connection for %s" % user_map[connection["user_id"]]
        )
    print("done")


def migrate_messages(source_db, dest_db):
    print("Migrating messages...")
    source = source_db.cursor(cursor_factory=DictCursor)
    dest = dest_db.cursor(cursor_factory=DictCursor)

    source.execute('SELECT id, email FROM "user"')
    user_map = {user["id"]: user["email"] for user in source}

    source.execute('SELECT id, name FROM "group"')
    team_map = {team["id"]: team["name"] for team in source}

    source.execute('SELECT id, user_id, "group_id", content FROM "messages"')
    for message in source:
        query = (
            "INSERT INTO message ("
            "content,"
            '"user",'
            "team"
            ") VALUES ("
            "%s, %s, %s"
            ") ON CONFLICT DO NOTHING",
            (
                message["content"],
                user_map[message["user_id"]],
                team_map[message["group_id"]],
            ),
        )
        dest.execute(query[0], query[1])
        print("    Added message #%s" % message["id"])
    print("done")


def migrate_settings(source_db, dest_db):
    print("Migrating settings...")
    source = source_db.cursor(cursor_factory=DictCursor)
    dest = dest_db.cursor(cursor_factory=DictCursor)

    source.execute('SELECT * FROM "settings"')
    for setting in source:
        query = (
            "INSERT INTO setting ("
            "key,"
            "description,"
            "value"
            ") VALUES ("
            "%s, %s, %s"
            ") ON CONFLICT DO NOTHING",
            (
                setting["key"],
                setting["description"],
                setting["value"],
            ),
        )
        dest.execute(query[0], query[1])
        print("    Added setting %s" % setting["key"])
    print("done")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("source_dsn")
    parser.add_argument("destination_dsn")
    parser.add_argument("--clean", action="store_true", default=False)
    args = parser.parse_args()

    with connect(args.source_dsn) as source_db:
        with connect(args.destination_dsn) as destination_db:
            add_users(source_db, destination_db)
            create_routes_from_directions(source_db, destination_db)
            migrate_teams(source_db, destination_db)
            migrate_stations(source_db, destination_db)
            migrate_connections(source_db, destination_db)
            migrate_messages(source_db, destination_db)
            migrate_settings(source_db, destination_db)
            destination_db.commit()
