# Deployment Documentation

This document describes how to deploy the powonline stack on a vanilla Docker host using Traefik as the reverse proxy.

## Architecture

*   **Database**: PostgreSQL 17 (standard image).
*   **Backend (API)**: FastAPI application running with Uvicorn.
*   **Frontend**: Vue.js SPA served by Nginx.

## Configuration

The application is configured using a mix of an INI file and environment variables.

### Backend (API)

*   **Config File**: Mount an `app.ini` to `/etc/powonline/app.ini`.
*   **Env Overrides**:
    *   `POWONLINE_DSN`: PostgreSQL connection string (`postgresql+psycopg://...`).
    *   `POWONLINE_JWT_SECRET`: Secret for signing tokens.
    *   `POWONLINE_ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins.
    *   `POWONLINE_GOOGLE_CLIENT_SECRET`: (Optional) Secret for Google OAuth.
    *   `POWONLINE_OIDC_CLIENT_SECRET`: (Optional) Secret for Generic OIDC.

### Frontend

*   **Env Variables**:
    *   `BACKEND_URL`: The public URL of the API (e.g., `https://api.powonline.example.com`).

## Volumes

*   `db_data`: Persistent storage for PostgreSQL.
*   `uploads`: Persistent storage for user-uploaded files (backend).

## Bootstrapping Admin

Initial deployment requires creating an admin user. Run the following command inside the `api` container:

```bash
docker compose exec api python3 -m powonline.bootstrap_admin <username> <password>
```

This will create the user (or update their password) and assign the `admin` role.

## Traefik Integration

The stack expects Traefik to handle TLS termination. Use standard labels for routing:

```yaml
services:
  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.powonline-api.rule=Host(`api.example.com`)"
      - "traefik.http.routers.powonline-api.entrypoints=websecure"
      - "traefik.http.routers.powonline-api.tls.certresolver=myresolver"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.powonline-fe.rule=Host(`powonline.example.com`)"
      - "traefik.http.routers.powonline-fe.entrypoints=websecure"
      - "traefik.http.routers.powonline-fe.tls.certresolver=myresolver"
```

## Local Development / Smoke Testing

To spin up the full stack locally (database + API, with optional frontend) for
smoke-testing, see [Local Stack](./local-stack.md).  That guide covers:

- Starting the stack with `docker compose`
- Wiring in the frontend (dev server or container)
- Admin bootstrapping
- Available environment variables

## Identity Providers (OIDC)

See the detailed configuration for each provider:

*   [Google](./providers/google.md)
*   [GitHub](./providers/github.md)
*   [Facebook](./providers/facebook.md)
*   [Microsoft](./providers/microsoft.md)
*   [Generic OIDC](./providers/oidc.md)
