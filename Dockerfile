# =============================================================================
# Stage 1 — build
#   Install dependencies and the application into an isolated virtualenv.
#   Uses uv for fast, reproducible, lockfile-driven installs.
# =============================================================================
FROM python:3.12-slim AS build

# Install uv from the official distroless image — no pip round-trip needed.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Layer-cache dependencies: copy lockfiles before source so this layer is only
# invalidated when dependencies actually change.
COPY README.rst pyproject.toml uv.lock ./

# Sync production dependencies into /app/.venv (no dev extras).
RUN uv sync --frozen --no-dev --no-install-project

# Now copy the application source and install it (no-deps: deps already synced).
COPY src/ ./src/
RUN uv pip install --python /app/.venv/bin/python --no-deps .

# Copy migration assets that the runtime container needs.
COPY alembic/ ./alembic/
COPY alembic.ini ./

# =============================================================================
# Stage 2 — runtime
#   Minimal image containing only what is needed to run the application.
# =============================================================================
FROM python:3.12-slim AS runtime

# Bake the source commit SHA into the image so /healthz can report it.
# Pass at build time with: --build-arg COMMIT_SHA=$(git rev-parse HEAD)
ARG COMMIT_SHA=unknown
ENV COMMIT_SHA=${COMMIT_SHA}

# Create a non-root user/group for the application process.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --no-create-home appuser

# Copy the virtualenv produced in the build stage.
COPY --from=build /app/.venv /opt/powonline

# Copy database migration assets.
COPY --from=build /app/alembic /alembic/alembic
COPY --from=build /app/alembic.ini /alembic/alembic.ini

# Copy entrypoint scripts from the repository.
COPY containers/main/resources/start.bash /start.bash
COPY containers/main/resources/migrate.bash /migrate.bash
COPY containers/main/resources/seed.bash /seed.bash

# Copy scripts that are run inside the container but are not part of the
# installed package (e.g. data-seeding utilities).
COPY scripts/ /scripts/

# Rewrite shebangs in venv scripts that were baked with the build-stage path
# (/app/.venv/...) so they resolve correctly from /opt/powonline/... at runtime.
RUN find /opt/powonline/bin -maxdepth 1 -type f \
    | xargs -r grep -rlF '/app/.venv' \
    | xargs -r sed -i 's|/app/.venv|/opt/powonline|g'

# Prepare a writable uploads directory owned by the application user.
# At runtime, mount a named volume over /var/lib/powonline/uploads.
RUN chmod +x /start.bash /migrate.bash /seed.bash \
    && chown -R appuser:appgroup /alembic \
    && mkdir -p /var/lib/powonline/uploads \
    && chown -R appuser:appgroup /var/lib/powonline

# Drop privileges.
USER appuser

EXPOSE 8000

ENTRYPOINT ["/start.bash"]
