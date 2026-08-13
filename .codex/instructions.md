# Cisco NMS Engineering Instructions

## Product boundary

This is a local, single-user Cisco IOS/IOS-XE switch management application.
It manages inventory and explicit operator actions. It is not a monitoring
platform.

Do not add unless explicitly requested: SNMP polling, Prometheus, Grafana,
alerts, NetFlow, syslog collection, scheduled polling, background workers,
Redis, Celery, Kubernetes, or microservices.

## Stack and ownership

- Backend: Python, FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL,
  Netmiko.
- Frontend: React, TypeScript, Vite, Cytoscape.js.
- Runtime: Docker Compose with `web`, `api`, and `postgres`.
- Keep API routes thin. Put Cisco/SSH/network behavior in services.
- Use SQLAlchemy ORM and Alembic migrations for schema changes.
- Use type hints in Python and tests for security-sensitive or parsing code.
- Prefer existing local patterns and small, maintainable changes.

## Security requirements

- Never store, return, log, or commit private-key contents.
- Mount only the dedicated NMS key directory read-only at `/run/ssh-keys`.
- Never mount the host's entire `~/.ssh` directory.
- Treat SSH configuration, CLI output, neighbor names, and configuration
  commands as untrusted input. Never execute SSH config through a shell.
- `IdentityFile` must remain under the configured host allowlist after path
  normalization; reject traversal and symlinks resolving outside the mounted
  key directory.
- Sanitize Netmiko, Paramiko, filesystem, and database errors before returning
  them to the client or logging them.
- Preserve PostgreSQL as an internal-only service. Only `web` publishes a
  localhost port by default.
- Configuration previews must validate bounded commands and use an expiring,
  device-bound confirmation token. Never execute commands from initial form
  submission.
- Network actions are explicit requests only. Do not add polling or schedulers.

## UI requirements

Use the existing dark graphite enterprise visual language with restrained blue
accents, compact typography, subtle borders, dense tables, and professional
topology/device surfaces. Use the existing component and icon patterns. Do not
invent live status or monitoring data. Device interface state must come only
from the latest explicit refresh response.

Keep text inside its controls and responsive layouts. Do not introduce
marketing-style landing pages, decorative blobs, copied Cisco hardware/marks,
or nested card layouts.

## Change procedure

1. Read this file, `docs/PLAN.md`, and `docs/architecture.md`.
2. Inspect the current implementation and working tree before editing.
3. Define the smallest change that satisfies the request.
4. Update affected docs and Alembic migrations with schema changes.
5. Run backend tests: `backend/.venv/bin/pytest -q`.
6. Run frontend build: `(cd frontend && npm run build)`.
7. Validate Compose when infrastructure changes:
   `docker compose config --quiet` with required `.env` values.
8. Check `git diff --check`, review secrets/private-key exposure, and leave
   unrelated user changes untouched.
9. Summarize changes, tests, warnings, and remaining risks.

Do not automatically invent a next phase. Work only on the user's current
request. Commit and push only when the user asks for it or the established
working session explicitly includes that step.

## Runtime facts

- Local start: `cp .env.example .env`, set real secrets and key directory,
  then `docker compose up -d --build`.
- Browser: `http://127.0.0.1:8080`.
- Stop: `docker compose down`.
- Destructive local data reset: `docker compose down -v`, only with explicit
  operator intent.
- Full security precautions: `docs/security.md`.
- Release checks: `docs/release-checklist.md`.
