# Cisco NMS Engineering Instructions

## Product Boundary

This is a local, single-user Cisco IOS/IOS-XE switch management application.
It manages inventory and explicit operator actions. It is not a monitoring
platform.

Do not add unless explicitly requested: SNMP polling, Prometheus, Grafana,
alerts, NetFlow, syslog collection, scheduled polling, background workers,
Redis, Celery, Kubernetes, or microservices.

## Stack And Ownership

- Backend: Python, FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL,
  Netmiko.
- Frontend: React, TypeScript, Vite, Cytoscape.js.
- Runtime: Docker Compose with `web`, `api`, and `postgres`.
- Keep API routes thin. Put Cisco, SSH, and network behavior in services.
- Use SQLAlchemy ORM and Alembic migrations for schema changes.
- Use Python type hints and tests for security-sensitive or parsing code.
- Prefer existing local patterns and small, maintainable changes.

## Security Requirements

- Never store, return, log, or commit private-key contents.
- Mount only the dedicated NMS key directory read-only at `/run/ssh-keys`.
- Never mount the host's entire `~/.ssh` directory.
- Treat SSH configuration, CLI output, neighbor names, and configuration
  commands as untrusted input. Never execute SSH config through a shell.
- `IdentityFile` must remain under the configured host allowlist after path
  normalization; reject traversal and symlinks resolving outside the mounted
  key directory.
- Sanitize Netmiko, Paramiko, filesystem, and database errors before returning
  them to clients or logging them.
- Keep PostgreSQL internal-only. Only `web` publishes a localhost port by
  default.
- Configuration previews must validate bounded commands and use an expiring,
  device-bound confirmation token. Never execute commands from initial form
  submission.
- Network actions are explicit requests only. Do not add polling or schedulers.

## UI Requirements

Use the existing dark graphite enterprise visual language with restrained blue
accents, compact typography, subtle borders, dense tables, and professional
topology/device surfaces. Use existing component and icon patterns. Do not
invent live status or monitoring data. Device interface state must come only
from the latest explicit refresh response.

Keep text inside controls and responsive layouts. Do not introduce
marketing-style landing pages, decorative blobs, copied Cisco hardware/marks,
or nested card layouts.

## Change Procedure

1. Read this file, `PLAN.md`, and `../architecture.md`.
2. Inspect the implementation and working tree before editing.
3. Define the smallest change that satisfies the request.
4. Update affected docs and Alembic migrations with schema changes.
5. Run `backend/.venv/bin/pytest -q`.
6. Run `(cd frontend && npm run build)`.
7. For infrastructure changes, run `docker compose config --quiet` with the
   required `.env` values.
8. Run `git diff --check` and review secrets/private-key exposure.
9. Summarize changes, tests, warnings, and remaining risks.

Do not automatically invent a next phase. Work only on the current request.
Commit and push only when the user asks or the active work explicitly includes
that step.

## Runtime Facts

- Start: `cp .env.example .env`, set secrets/key directory, then
  `docker compose up -d --build`.
- Browser: `http://127.0.0.1:8080`.
- Stop: `docker compose down`.
- Destructive local reset: `docker compose down -v`, only with explicit intent.
- Security: `security.md`.
- Release checks: `release-checklist.md`.
