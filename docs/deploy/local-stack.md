# Local Stack — Full-Stack Smoke Testing

This guide explains how to spin up the complete powonline stack (database +
backend API + optional frontend) on a local machine for smoke-testing without
needing a remote environment.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (v2)
- A copy of the backend config file (see step 1 below)

## Quick Start (Backend Only)

The API can be exercised without the frontend via any HTTP client (browser,
curl, Postman, etc.).

### 1. Create a local config file

```bash
# From the backend/ directory:
cp sample-files/app.ini config/app.ini
```

Edit `config/app.ini` as needed.  At minimum review:

- `[powonline]` → `upload_folder`
- `[auth]` → `jwt_secret` (or override via `POWONLINE_JWT_SECRET` env var)
- Any social-login sections you want to enable

### 2. Start the stack

```bash
# From the backend/ directory:
docker compose -f docs/deploy/docker-compose.local.yml up --build
```

This will:

1. Start a PostgreSQL 17 database.
2. Build the API image from the local `Dockerfile`.
3. Start the API, running database migrations automatically on boot.
4. Run the `bootstrap` one-shot container which seeds an initial admin user
   (`admin` / `admin` by default — see [Admin Bootstrap](#admin-bootstrap)).

The API will be available at <http://localhost:8000>.
Interactive API docs are at <http://localhost:8000/docs>.

### 3. Stop the stack

```bash
docker compose -f docs/deploy/docker-compose.local.yml down        # keep volumes
docker compose -f docs/deploy/docker-compose.local.yml down -v     # wipe volumes
```

---

## Adding the Frontend for Full-Stack Smoke Testing

The frontend is a separate component and is **not** included in this stack by
default.  You have two options:

### Option A — Frontend dev server on the host (recommended for development)

```bash
# From the frontend source directory:
npm install
BACKEND_URL=http://localhost:8000 npm run dev
```

The Vite / webpack dev server typically binds to <http://localhost:8080>.

Make sure `POWONLINE_ALLOWED_ORIGINS` in your `.env` (or in the compose file)
includes `http://localhost:8080` so the API accepts CORS requests from the
browser.

### Option B — Frontend container alongside the API

1. Build the frontend image from source:

   ```bash
   docker build -t powonline-frontend ../frontend
   ```

   Or pull it from your registry.

2. Edit `docs/deploy/docker-compose.local.yml` and uncomment the `frontend`
   service block near the bottom of the file.  Adjust the `image:` or
   `build:` stanza to match how you built/tagged the image.

3. Restart the stack:

   ```bash
   docker compose -f docs/deploy/docker-compose.local.yml up --build
   ```

   The frontend will be available at <http://localhost:8080>.

---

## Admin Bootstrap

The `bootstrap` service creates the initial admin user when the stack first
starts.  Defaults:

| Variable | Default |
|---|---|
| `ADMIN_USER` | `admin` |
| `ADMIN_PASSWORD` | `admin` |

Override them by creating a `.env` file next to the compose file:

```dotenv
ADMIN_USER=myuser
ADMIN_PASSWORD=s3cr3t
```

You can also bootstrap manually at any time:

```bash
docker compose -f docs/deploy/docker-compose.local.yml exec api \
  python3 -m powonline.bootstrap_admin <username> <password>
```

---

## Environment Variables Reference

All variables below can be set in a `.env` file placed in the same directory
as the compose file, or exported in your shell.

| Variable | Default | Description |
|---|---|---|
| `DB_PASSWORD` | `localdev` | PostgreSQL password |
| `ADMIN_USER` | `admin` | Initial admin username |
| `ADMIN_PASSWORD` | `admin` | Initial admin password |
| `POWONLINE_JWT_SECRET` | `local-dev-jwt-secret-change-me` | Token signing secret |
| `POWONLINE_ALLOWED_ORIGINS` | `http://localhost:8080` | Comma-separated CORS origins |
| `POWONLINE_GOOGLE_CLIENT_SECRET` | *(empty)* | Google OAuth secret (disables Google login if empty) |
| `POWONLINE_OIDC_CLIENT_SECRET` | *(empty)* | Generic OIDC secret |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL injected into the frontend container |

---

## Volumes

| Volume | Purpose |
|---|---|
| `db_data` | PostgreSQL data directory |
| `uploads` | User-uploaded files served by the API |

Both volumes are created automatically by Docker Compose.  Pass `-v` to
`docker compose down` to remove them and start fresh.
