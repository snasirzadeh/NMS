# Release Checklist

## Source and secrets

- [ ] `git status` is clean except for intentional release changes.
- [ ] No private keys, credentials, real device data, or populated `.env` files
      are committed.
- [ ] `.env.example` contains placeholders only.
- [ ] `git grep` shows no legacy `NMS_SSH_PRIVATE_KEY` runtime configuration.

## Runtime

- [ ] Set unique `POSTGRES_PASSWORD` and `NMS_CONFIG_CONFIRMATION_SECRET` in
      the deployment `.env`.
- [ ] Set `NMS_SSH_KEYS_HOST_DIR` to the dedicated key directory.
- [ ] Verify key directory and private-key permissions.
- [ ] Confirm only `web` publishes `127.0.0.1:8080`.
- [ ] Confirm API and PostgreSQL have no host-published ports.
- [ ] Confirm the key mount is read-only and contains only dedicated NMS keys.
- [ ] Run `docker compose config --quiet` with deployment environment values.
- [ ] Run `docker compose up -d --build` and verify both health endpoints.

## Application checks

- [ ] Run `backend/.venv/bin/pytest -q`.
- [ ] Run `(cd frontend && npm run build)`.
- [ ] Apply and verify Alembic migrations.
- [ ] Create a group and device using a valid SSH configuration.
- [ ] Test SSH, refresh device data, and verify Interfaces/VLANs/Neighbors.
- [ ] Run explicit topology discovery and inspect managed/unmanaged nodes.
- [ ] Create and view a manual configuration backup.
- [ ] Verify configuration preview rejects unsafe input and does not execute
      commands.

## Operations

- [ ] Create a PostgreSQL logical backup before upgrades.
- [ ] Record the application commit and migration head used for deployment.
- [ ] Review logs for sanitized errors only; never collect raw SSH config,
      private-key contents, or sensitive device output in release artifacts.
- [ ] Document rollback and database-restore ownership for the local operator.
