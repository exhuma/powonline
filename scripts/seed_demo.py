#!/usr/bin/env python
"""
Pre-production demo data seed.

Populates the database with three events, 20 teams each, shared stations,
questionnaires, and 10 role-named demo users (password: "demo").

Usage (repo root, venv active, POWONLINE_DSN set):
    python scripts/seed_demo.py           # idempotent upsert
    python scripts/seed_demo.py --reset   # delete all demo data first, then seed

Inside the container the wrapper /seed.bash calls this script via
/opt/powonline/bin/python.
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# The powonline package must be installed (editable or otherwise).
# In the container: /opt/powonline/bin/python
# Locally:         activate the project venv, then run directly.
# ---------------------------------------------------------------------------
try:
    from powonline.model import (
        Event,
        EventUserRole,
        Questionnaire,
        Role,
        Route,
        Station,
        Team,
        User,
        get_dsn,
        route_station_table,
        user_station_table,
    )
except ModuleNotFoundError:
    sys.exit(
        "ERROR: 'powonline' package not found.\n"
        "Install it first:  pip install -e .  (or uv sync)"
    )

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEMO_PASSWORD = "demo"

# Sentinel prefix — every demo row carries this so --reset can find them all.
PFX = "demo-"

# ---------------------------------------------------------------------------
# Demo users
# (username, [global role names])
# ---------------------------------------------------------------------------
DEMO_USERS: list[tuple[str, list[str]]] = [
    ("demo-admin", ["admin"]),
    ("demo-staff-1", ["staff"]),
    ("demo-staff-2", ["staff"]),
    ("demo-station-manager-1", ["station_manager"]),
    ("demo-station-manager-2", ["station_manager"]),
    ("demo-station-manager-3", ["station_manager"]),
    # Per-event roles are assigned later; no global role for these.
    ("demo-event-owner-1", []),
    ("demo-event-owner-2", []),
    ("demo-event-co-admin", []),
    # A plain viewer — tests public / read-only endpoints.
    ("demo-viewer", []),
]

# ---------------------------------------------------------------------------
# Event 1 — "Sommer-Rally 2026"
# Simple recurring-event layout: two routes, all stations shared, 50/50 split.
# ---------------------------------------------------------------------------
EVENT1_NAME = "demo-sommer-rally-2026"
EVENT1_TITLE = "Sommer-Rally 2026"
EVENT1_RANGE = Range(
    datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
    datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
)

EVENT1_ROUTES = [
    ("demo-sr-route-red", "#e74c3c"),
    ("demo-sr-route-blue", "#2980b9"),
]

# (name, order, is_start, is_end)
EVENT1_STATIONS = [
    ("demo-sr-start", 1, True, False),
    ("demo-sr-checkpoint-1", 2, False, False),
    ("demo-sr-checkpoint-2", 3, False, False),
    ("demo-sr-checkpoint-3", 4, False, False),
    ("demo-sr-checkpoint-4", 5, False, False),
    ("demo-sr-checkpoint-5", 6, False, False),
    ("demo-sr-checkpoint-6", 7, False, False),
    ("demo-sr-finish", 8, False, True),
]

# Teams 1–10 on red, 11–20 on blue.
EVENT1_TEAMS = [
    (
        f"demo-sr-team-{i:02d}",
        "demo-sr-route-red" if i <= 10 else "demo-sr-route-blue",
    )
    for i in range(1, 21)
]

# One questionnaire per station (same order as the station).
EVENT1_QUESTIONNAIRES = [
    (f"demo-sr-quiz-{sname.removeprefix('demo-sr-')}", 20, idx + 1, sname)
    for idx, (sname, *_) in enumerate(EVENT1_STATIONS)
]

# Station manager assignments for event 1 (user → [station names])
EVENT1_STATION_MANAGERS = {
    "demo-station-manager-1": [
        "demo-sr-start",
        "demo-sr-checkpoint-1",
        "demo-sr-checkpoint-2",
    ],
    "demo-station-manager-2": [
        "demo-sr-checkpoint-3",
        "demo-sr-checkpoint-4",
        "demo-sr-checkpoint-5",
    ],
    "demo-station-manager-3": [
        "demo-sr-checkpoint-6",
        "demo-sr-finish",
    ],
}

# ---------------------------------------------------------------------------
# Event 2 — "Adventure Cup 2026"
# Complex route setup: 4 routes, 12 stations with partial sharing.
# ---------------------------------------------------------------------------
EVENT2_NAME = "demo-adventure-cup-2026"
EVENT2_TITLE = "Adventure Cup 2026"
EVENT2_RANGE = Range(
    datetime(2026, 9, 12, 7, 0, tzinfo=timezone.utc),
    datetime(2026, 9, 12, 19, 0, tzinfo=timezone.utc),
)

EVENT2_ROUTES = [
    ("demo-ac-route-north", "#27ae60"),
    ("demo-ac-route-south", "#e67e22"),
    ("demo-ac-route-east", "#8e44ad"),
    ("demo-ac-route-west", "#16a085"),
]

# (name, order, is_start, is_end)
EVENT2_STATIONS = [
    ("demo-ac-base-camp", 1, True, False),  # shared start — all 4 routes
    ("demo-ac-forest-crossing", 2, False, False),  # north + west
    ("demo-ac-river-ford", 3, False, False),  # north + west
    ("demo-ac-cliff-path", 2, False, False),  # north + east
    ("demo-ac-ravine-bridge", 3, False, False),  # north + east
    ("demo-ac-swamp-path", 2, False, False),  # south + west
    ("demo-ac-meadow", 3, False, False),  # south + west
    ("demo-ac-canyon", 2, False, False),  # south + east
    ("demo-ac-waterfall", 3, False, False),  # south + east
    ("demo-ac-cave", 4, False, False),  # north only
    ("demo-ac-ancient-ruins", 4, False, False),  # south only
    ("demo-ac-summit", 5, False, True),  # shared finish — all 4 routes
]

# route → station names it visits
EVENT2_ROUTE_STATIONS: dict[str, list[str]] = {
    "demo-ac-route-north": [
        "demo-ac-base-camp",
        "demo-ac-forest-crossing",
        "demo-ac-river-ford",
        "demo-ac-cliff-path",
        "demo-ac-ravine-bridge",
        "demo-ac-cave",
        "demo-ac-summit",
    ],
    "demo-ac-route-south": [
        "demo-ac-base-camp",
        "demo-ac-swamp-path",
        "demo-ac-meadow",
        "demo-ac-canyon",
        "demo-ac-waterfall",
        "demo-ac-ancient-ruins",
        "demo-ac-summit",
    ],
    "demo-ac-route-east": [
        "demo-ac-base-camp",
        "demo-ac-cliff-path",
        "demo-ac-ravine-bridge",
        "demo-ac-canyon",
        "demo-ac-waterfall",
        "demo-ac-summit",
    ],
    "demo-ac-route-west": [
        "demo-ac-base-camp",
        "demo-ac-forest-crossing",
        "demo-ac-river-ford",
        "demo-ac-swamp-path",
        "demo-ac-meadow",
        "demo-ac-summit",
    ],
}

# 5 teams per route
EVENT2_TEAMS = (
    [
        (f"demo-ac-north-team-{i:02d}", "demo-ac-route-north")
        for i in range(1, 6)
    ]
    + [
        (f"demo-ac-south-team-{i:02d}", "demo-ac-route-south")
        for i in range(1, 6)
    ]
    + [
        (f"demo-ac-east-team-{i:02d}", "demo-ac-route-east")
        for i in range(1, 6)
    ]
    + [
        (f"demo-ac-west-team-{i:02d}", "demo-ac-route-west")
        for i in range(1, 6)
    ]
)

# One questionnaire per station
EVENT2_QUESTIONNAIRES = [
    (
        f"demo-ac-quiz-{sname.removeprefix('demo-ac-')}",
        25,
        idx + 1,
        sname,
    )
    for idx, (sname, *_) in enumerate(EVENT2_STATIONS)
]

# ---------------------------------------------------------------------------
# Event 3 — "Winter Challenge 2027"
# Future event — tests time-window gating; no event owner assigned.
# ---------------------------------------------------------------------------
EVENT3_NAME = "demo-winter-challenge-2027"
EVENT3_TITLE = "Winter Challenge 2027"
EVENT3_RANGE = Range(
    datetime(2027, 1, 15, 9, 0, tzinfo=timezone.utc),
    datetime(2027, 1, 15, 18, 0, tzinfo=timezone.utc),
)

EVENT3_ROUTES = [
    ("demo-wc-route-silver", "#bdc3c7"),
    ("demo-wc-route-gold", "#f39c12"),
]

EVENT3_STATIONS = [
    ("demo-wc-start", 1, True, False),
    ("demo-wc-ice-crossing", 2, False, False),
    ("demo-wc-frozen-lake", 3, False, False),
    ("demo-wc-snow-peak", 4, False, False),
    ("demo-wc-glacier-pass", 5, False, False),
    ("demo-wc-finish", 6, False, True),
]

EVENT3_TEAMS = [
    (
        f"demo-wc-team-{i:02d}",
        "demo-wc-route-silver" if i <= 10 else "demo-wc-route-gold",
    )
    for i in range(1, 21)
]

EVENT3_QUESTIONNAIRES = [
    (
        f"demo-wc-quiz-{sname.removeprefix('demo-wc-')}",
        15,
        idx + 1,
        sname,
    )
    for idx, (sname, *_) in enumerate(EVENT3_STATIONS)
]


# ===========================================================================
# Helpers
# ===========================================================================


async def _get_or_create_event(
    session, name: str, title: str, time_range: Range
) -> Event:
    result = await session.execute(select(Event).filter_by(name=name))
    event = result.scalar_one_or_none()
    if event is None:
        event = Event(name=name, title=title, time_range=time_range)
        session.add(event)
        await session.flush()  # populate event.id
        LOG.info("  Created event '%s'", name)
    else:
        LOG.info("  Event '%s' already exists — skipping creation", name)
    return event


async def _get_or_create_route(
    session, name: str, color: str, event_id: int
) -> Route:
    result = await session.execute(
        select(Route).filter_by(name=name, event_id=event_id)
    )
    route = result.scalar_one_or_none()
    if route is None:
        route = Route(name=name, color=color, event_id=event_id)
        session.add(route)
        LOG.info("    Route '%s'", name)
    return route


async def _get_or_create_station(
    session,
    name: str,
    event_id: int,
    order: int,
    is_start: bool,
    is_end: bool,
) -> Station:
    result = await session.execute(
        select(Station).filter_by(name=name, event_id=event_id)
    )
    station = result.scalar_one_or_none()
    if station is None:
        station = Station(
            name=name,
            event_id=event_id,
            order=order,
            is_start=is_start,
            is_end=is_end,
        )
        session.add(station)
        LOG.info("    Station '%s'", name)
    return station


async def _get_or_create_team(
    session, name: str, route_name: str, event_id: int
) -> Team:
    result = await session.execute(
        select(Team).filter_by(name=name, event_id=event_id)
    )
    team = result.scalar_one_or_none()
    if team is None:
        team = Team(
            name=name,
            route_name=route_name,
            event_id=event_id,
            email=f"{name}@demo.example",
            is_confirmed=True,
            accepted=True,
            confirmation_key=token_urlsafe(16),
        )
        session.add(team)
    return team


async def _get_or_create_questionnaire(
    session,
    name: str,
    max_score: int,
    order: int,
    station_name: str,
    event_id: int,
) -> Questionnaire:
    result = await session.execute(
        select(Questionnaire).filter_by(name=name, event_id=event_id)
    )
    q = result.scalar_one_or_none()
    if q is None:
        q = Questionnaire(
            name=name,
            max_score=max_score,
            order=order,
            station_name=station_name,
        )
        q.event_id = event_id
        session.add(q)
        LOG.info("    Questionnaire '%s' → station '%s'", name, station_name)
    return q


async def _link_route_station(session, route_name, station_name, event_id):
    """Insert into the route_station junction table (idempotent)."""
    exists = await session.execute(
        select(route_station_table).where(
            route_station_table.c.route_name == route_name,
            route_station_table.c.station_name == station_name,
            route_station_table.c.event_id == event_id,
        )
    )
    if exists.first() is None:
        await session.execute(
            route_station_table.insert().values(
                route_name=route_name,
                station_name=station_name,
                event_id=event_id,
            )
        )


async def _link_user_station(session, user_name, station_name, event_id):
    """Insert into user_station junction table (idempotent)."""
    exists = await session.execute(
        select(user_station_table).where(
            user_station_table.c.user_name == user_name,
            user_station_table.c.station_name == station_name,
            user_station_table.c.event_id == event_id,
        )
    )
    if exists.first() is None:
        await session.execute(
            user_station_table.insert().values(
                user_name=user_name,
                station_name=station_name,
                event_id=event_id,
            )
        )


async def _assign_event_role(
    session, event_id: int, user_name: str, role_name: str
):
    result = await session.execute(
        select(EventUserRole).filter_by(
            event_id=event_id, user_name=user_name, role_name=role_name
        )
    )
    if result.scalar_one_or_none() is None:
        session.add(
            EventUserRole(
                event_id=event_id, user_name=user_name, role_name=role_name
            )
        )
        LOG.info(
            "    EventUserRole: %s → %s (event %d)",
            user_name,
            role_name,
            event_id,
        )


# ===========================================================================
# Reset
# ===========================================================================


async def reset(session) -> None:
    """Delete all rows whose name starts with 'demo-'."""
    LOG.info("--- RESET: removing existing demo data ---")

    # Events cascade-delete all child rows (teams, stations, routes,
    # questionnaires, event_user_role, etc.) via ON DELETE CASCADE.
    result = await session.execute(
        select(Event).where(Event.name.like(f"{PFX}%"))
    )
    for event in result.scalars():
        LOG.info("  Deleting event '%s' and all its children", event.name)
        await session.delete(event)

    # Users (no cascade from event → user, delete explicitly).
    result = await session.execute(
        select(User).where(User.name.like(f"{PFX}%"))
    )
    for user in result.scalars():
        LOG.info("  Deleting user '%s'", user.name)
        await session.delete(user)

    await session.flush()
    LOG.info("--- RESET complete ---")


# ===========================================================================
# Seed
# ===========================================================================


async def seed_users(session) -> None:
    LOG.info("Seeding demo users …")
    for username, role_names in DEMO_USERS:
        result = await session.execute(select(User).filter_by(name=username))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(name=username, password=DEMO_PASSWORD)
            session.add(user)
            LOG.info("  Created user '%s'", username)
        else:
            LOG.info("  User '%s' already exists — updating password", username)
            user.setpw(DEMO_PASSWORD)

        await session.flush()

        user_roles = await user.awaitable_attrs.roles
        for rname in role_names:
            role = await Role.get_or_create(session, rname)
            if role not in user_roles:
                user_roles.add(role)
                LOG.info("    Assigned global role '%s'", rname)

    await session.flush()


async def seed_event1(session) -> Event:
    LOG.info("Seeding Event 1 — %s …", EVENT1_TITLE)
    event = await _get_or_create_event(
        session, EVENT1_NAME, EVENT1_TITLE, EVENT1_RANGE
    )
    eid = event.id

    # Routes
    for rname, color in EVENT1_ROUTES:
        await _get_or_create_route(session, rname, color, eid)
    await session.flush()

    # Stations (all shared between both routes)
    for sname, order, is_start, is_end in EVENT1_STATIONS:
        await _get_or_create_station(
            session, sname, eid, order, is_start, is_end
        )
    await session.flush()

    # Link every station to both routes
    for rname, _ in EVENT1_ROUTES:
        for sname, *_ in EVENT1_STATIONS:
            await _link_route_station(session, rname, sname, eid)

    # Teams
    for tname, rname in EVENT1_TEAMS:
        await _get_or_create_team(session, tname, rname, eid)
    await session.flush()

    # Questionnaires (one per station)
    for qname, max_score, order, sname in EVENT1_QUESTIONNAIRES:
        await _get_or_create_questionnaire(
            session, qname, max_score, order, sname, eid
        )
    await session.flush()

    # Station manager assignments
    for username, station_names in EVENT1_STATION_MANAGERS.items():
        for sname in station_names:
            await _link_user_station(session, username, sname, eid)

    # Per-event role
    await _assign_event_role(session, eid, "demo-event-owner-1", "event_owner")
    await session.flush()

    return event


async def seed_event2(session) -> Event:
    LOG.info("Seeding Event 2 — %s …", EVENT2_TITLE)
    event = await _get_or_create_event(
        session, EVENT2_NAME, EVENT2_TITLE, EVENT2_RANGE
    )
    eid = event.id

    # Routes
    for rname, color in EVENT2_ROUTES:
        await _get_or_create_route(session, rname, color, eid)
    await session.flush()

    # Stations
    for sname, order, is_start, is_end in EVENT2_STATIONS:
        await _get_or_create_station(
            session, sname, eid, order, is_start, is_end
        )
    await session.flush()

    # Partial route–station links
    for rname, station_names in EVENT2_ROUTE_STATIONS.items():
        for sname in station_names:
            await _link_route_station(session, rname, sname, eid)

    # Teams
    for tname, rname in EVENT2_TEAMS:
        await _get_or_create_team(session, tname, rname, eid)
    await session.flush()

    # Questionnaires
    for qname, max_score, order, sname in EVENT2_QUESTIONNAIRES:
        await _get_or_create_questionnaire(
            session, qname, max_score, order, sname, eid
        )
    await session.flush()

    # Per-event roles
    await _assign_event_role(session, eid, "demo-event-owner-2", "event_owner")
    await _assign_event_role(
        session, eid, "demo-event-co-admin", "event_co_admin"
    )
    await session.flush()

    return event


async def seed_event3(session) -> Event:
    LOG.info("Seeding Event 3 — %s …", EVENT3_TITLE)
    event = await _get_or_create_event(
        session, EVENT3_NAME, EVENT3_TITLE, EVENT3_RANGE
    )
    eid = event.id

    for rname, color in EVENT3_ROUTES:
        await _get_or_create_route(session, rname, color, eid)
    await session.flush()

    for sname, order, is_start, is_end in EVENT3_STATIONS:
        await _get_or_create_station(
            session, sname, eid, order, is_start, is_end
        )
    await session.flush()

    for rname, _ in EVENT3_ROUTES:
        for sname, *_ in EVENT3_STATIONS:
            await _link_route_station(session, rname, sname, eid)

    for tname, rname in EVENT3_TEAMS:
        await _get_or_create_team(session, tname, rname, eid)
    await session.flush()

    for qname, max_score, order, sname in EVENT3_QUESTIONNAIRES:
        await _get_or_create_questionnaire(
            session, qname, max_score, order, sname, eid
        )
    await session.flush()

    # No event owner assigned — intentionally tests admin-only access.
    return event


# ===========================================================================
# Entry point
# ===========================================================================


async def async_main(do_reset: bool) -> None:
    dsn = get_dsn()
    if not dsn:
        sys.exit("ERROR: POWONLINE_DSN environment variable is not set.")

    engine = create_async_engine(dsn, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            if do_reset:
                await reset(session)

            await seed_users(session)
            await seed_event1(session)
            await seed_event2(session)
            await seed_event3(session)

    await engine.dispose()
    LOG.info("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the database with pre-production demo data."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all demo-prefixed rows before seeding (clean slate).",
    )
    args = parser.parse_args()
    asyncio.run(async_main(args.reset))


if __name__ == "__main__":
    main()
