# Cisco NMS Engineering Instructions

## Product boundary

This is a local, single-user Cisco IOS/IOS-XE management application. Network
work occurs only for explicit operator requests. Do not add polling, schedulers,
workers, Redis, Celery, monitoring, alerts, metrics, syslog, or microservices.

## Stack and ownership

- FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL, Netmiko/Paramiko
- React, TypeScript, Vite, Cytoscape.js
- Docker Compose services: `web`, `api`, `postgres`
- Keep routes thin; put authentication, vault, credentials, SSH, and Cisco
  behavior in their dedicated services.

## Security requirements

- Passwords are Argon2id hashes, never reversible values.
- Vault encryption uses a random master key wrapped by a separately derived
  Argon2id KEK; credential encryption uses AES-256-GCM with fresh nonces.
- Never return or log password hashes, passwords, KEKs, vault keys, private
  keys, passphrases, encrypted credential payloads, or session secrets.
- Use dedicated API response schemas. Never serialize credential ORM objects.
- Keep sessions server-side with HttpOnly SameSite cookies and CSRF validation.
- Reject unknown SSH host keys pending explicit trust and block changed keys.
- Legacy SSH algorithms are device-scoped only.
- Do not add external key paths, host SSH mounts, or agent integration.
- Keep PostgreSQL internal-only and only web host-published.

## UI requirements

Keep the dark graphite enterprise visual language. Credentials are write-only
after save. Device state must be subtle and based only on the latest explicit
SSH operation; never imply live monitoring.

## Change procedure

1. Read `docs/README.md`, this file, `docs/PLAN.md`, and
   `docs/architecture.md`.
2. Inspect the implementation and worktree before editing.
3. Update Alembic migrations and affected documentation with schema changes.
4. Run backend tests, frontend build, Compose validation, `git diff --check`,
   and a repository-wide stale-architecture search.
5. Commit or push only when explicitly requested.
