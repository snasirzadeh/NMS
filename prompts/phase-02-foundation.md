# Phase 2 — Foundation

Read:
- `AGENTS.md`
- `docs/PLAN.md`
- `docs/architecture.md`

Implement Phase 2 only.

Build the application foundation:

Backend:
- FastAPI application structure
- configuration/settings module
- PostgreSQL connection
- SQLAlchemy base/session
- Alembic setup
- health endpoint
- structured logging foundation

Frontend:
- React + TypeScript + Vite
- application shell
- routing
- shared design tokens
- Cisco-inspired enterprise visual foundation

Infrastructure:
- working Dockerfiles
- working Docker Compose
- PostgreSQL health check
- backend health check if practical
- frontend reverse proxy
- localhost-only exposed application ports
- read-only SSH key directory mount

Requirements:
- `docker compose up -d` must start the stack
- PostgreSQL must not be exposed to the host
- private SSH key material must never be copied into an image
- do not implement real Cisco connections yet
- do not implement device CRUD yet

Run tests/builds and fix failures.

Update documentation for any changed startup commands.

Stop after Phase 2.
