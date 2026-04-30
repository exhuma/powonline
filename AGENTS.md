# AGENTS.md — Guidance for AI Agents and Contributors

This file documents operational tasks that require ongoing maintenance to keep
automated tooling aligned with the codebase.

---

## Demo Data Seed (`scripts/seed_demo.py`)

### Purpose

`scripts/seed_demo.py` populates the **pre-production** database with a
realistic but clearly-labelled dataset. Every row it creates uses the `demo-`
name prefix so demo data is trivially distinguishable from real data and can be
wiped cleanly with `--reset`.

The script is **not part of the installed package** — it lives in `scripts/`
and is never included in the distribution build.

### Running locally

```bash
# Prerequisites: venv active, POWONLINE_DSN points at the target database.
export POWONLINE_DSN=postgresql://powonline@localhost/powonline_preprod

# Idempotent upsert — safe to run repeatedly.
python scripts/seed_demo.py

# Wipe all demo-prefixed rows first, then re-seed (clean slate).
python scripts/seed_demo.py --reset
```

### Running in the container

The container exposes `/seed.bash` as a dedicated entry-point that delegates
to `/opt/powonline/bin/python /scripts/seed_demo.py`.

```bash
# One-off upsert
docker exec <container_name> /seed.bash

# Full reset + re-seed (used by the nightly cron job)
docker exec <container_name> /seed.bash --reset
```

The Ansible cron entry on the pre-prod host looks like:

```
0 2 * * * docker exec <container_name> /seed.bash --reset
```

> **Never run this against the production container.**  The script itself has
> no safeguard; that responsibility lies with the Ansible inventory targeting.

### What the seed creates

| Entity | Count | Notes |
|--------|-------|-------|
| Demo users | 10 | Password `demo` (bcrypt-hashed); see user table below |
| Events | 3 | See event descriptions below |
| Teams | 20 per event | `demo-*` prefix |
| Stations | 8 / 12 / 6 | Per event |
| Routes | 2 / 4 / 2 | Per event |
| Questionnaires | 1 per station | Linked via `station_name` |

**Demo users**

| Username | Global role | Per-event role |
|---|---|---|
| `demo-admin` | `admin` | — |
| `demo-staff-1` | `staff` | — |
| `demo-staff-2` | `staff` | — |
| `demo-station-manager-1` | `station_manager` | assigned to Event 1 stations |
| `demo-station-manager-2` | `station_manager` | assigned to Event 1 stations |
| `demo-station-manager-3` | `station_manager` | assigned to Event 1 stations |
| `demo-event-owner-1` | — | `event_owner` on Event 1 |
| `demo-event-owner-2` | — | `event_owner` on Event 2 |
| `demo-event-co-admin` | — | `event_co_admin` on Event 2 |
| `demo-viewer` | — | — |

**Events**

| Event name | Description |
|---|---|
| `demo-sommer-rally-2026` | Simple recurring-event layout: 2 routes, 8 stations shared between both, teams split 50/50. |
| `demo-adventure-cup-2026` | Complex layout: 4 routes, 12 stations with partial sharing across routes. |
| `demo-winter-challenge-2027` | Future event (time_range in 2027); tests time-window gating. No event owner. |

### When to update this script

Update `scripts/seed_demo.py` whenever any of the following change:

1. **A non-nullable column is added** to `Team`, `Station`, `Route`, `Event`,
   `Questionnaire`, or `User` — add the new field to the relevant
   `_get_or_create_*` helper and to every construction site in the seed.

2. **A column is renamed or removed** — update all references in the seed.

3. **A new role is introduced** in `powonline/auth.py` (`PERMISSION_MAP`) —
   consider adding a demo user that holds that role so the role can be
   exercised in pre-prod testing.

4. **The `User.__init__` signature changes** (e.g. after the bcrypt → argon2
   migration tracked in [issue #28](https://github.com/exhuma/powonline/issues/28))
   — update the `User(name=…, password=…)` call and any raw hash references.

5. **The `route_station` or `user_station` junction table gains new required
   columns** — update `_link_route_station` / `_link_user_station`.

6. **The `Event.time_range` column type changes** — update the
   `Range(datetime(…), datetime(…))` literals.

### Verifying the seed

After any schema or model change, confirm the seed still works:

```bash
# 1. Apply all migrations to a clean database.
alembic upgrade head

# 2. Run the seed (reset mode to start clean).
python scripts/seed_demo.py --reset

# 3. Run the test suite — it uses its own fixtures and must still pass.
pytest
```

Spot-check via psql:

```sql
SELECT name FROM event   WHERE name LIKE 'demo-%';
SELECT name FROM "user"  WHERE name LIKE 'demo-%';
SELECT count(*) FROM team WHERE name LIKE 'demo-%';
```

Expected: 3 events, 10 users, 60 teams.

### Naming convention

All rows created by the seed use the `demo-` prefix on their `name` field.
This convention is **load-bearing**: the `--reset` path uses
`WHERE name LIKE 'demo-%'` to scope deletions. Do not deviate from this prefix
when adding new seed data.

---

## Password hashing

Passwords are currently hashed with **bcrypt** (`model.py`).
Migration to **argon2** is tracked in
[issue #28](https://github.com/exhuma/powonline/issues/28).

When that migration lands:

- Update the `User(name=…, password=…)` constructor call in `seed_demo.py`
  if the hashing logic moves out of `User.__init__`.
- Update `tests/seed.sql` if it contains raw bcrypt hashes.
- Re-run the seed verification steps above.
