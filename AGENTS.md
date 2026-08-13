# AGENTS.md

## Project

This repository contains a local, single-user Network Management System for managing Cisco switches.

The application is intended to run only when needed with Docker Compose.

Before making architectural or feature changes, read:

1. `docs/PLAN.md`
2. `docs/architecture.md` if it exists
3. the prompt for the current phase under `prompts/`

## Core Stack

Backend:
- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- PostgreSQL
- Netmiko
- pyATS/Genie where useful

Frontend:
- React
- TypeScript
- Vite

Topology:
- Cytoscape.js or another suitable graph library

Infrastructure:
- Docker
- Docker Compose

## Scope

This is a management application, not a monitoring platform.

Do not add unless explicitly requested:
- SNMP polling
- Prometheus
- Grafana
- alerts
- NetFlow
- syslog collection
- scheduled polling
- background monitoring workers
- Redis
- Celery
- Kubernetes
- microservices

## Development Rules

- Keep API routes thin.
- Keep Cisco/network logic in service modules.
- Use type hints in Python.
- Use SQLAlchemy ORM and Alembic migrations.
- Write tests for security-sensitive and parsing code.
- Keep the application usable at the end of every phase.
- Do not rewrite working components without a concrete reason.
- Prefer simple, maintainable code over clever abstractions.

## SSH Security Rules

Cisco devices authenticate with SSH public/private keys.

- Never store private-key contents in PostgreSQL.
- Never store private-key contents in frontend state.
- Never return private-key contents from the API.
- Never log private-key contents.
- Never commit private keys.
- Private key directories must be mounted read-only into the backend container.
- Treat device-provided SSH configuration as untrusted input.
- Do not execute SSH config text through a shell.
- Reject IdentityFile paths outside the configured allowlist.
- Reject path traversal.
- Sanitize network/SSH exceptions before returning them through the API.

A device may contain an OpenSSH config block such as:

```ssh
Host cisco-sw1
    HostName 192.168.35.10
    User cisco
    IdentityFile ~/.ssh/keys/cisco
    IdentitiesOnly yes

    KexAlgorithms +diffie-hellman-group14-sha1
    HostKeyAlgorithms +ssh-rsa
    PubkeyAcceptedAlgorithms +ssh-rsa
```

The host-side IdentityFile path must be mapped safely to the read-only key directory available inside the backend container.

## UI Direction

The UI must feel like a polished commercial network-management product.

Use an original Cisco-inspired enterprise networking aesthetic:
- dark graphite device panels
- restrained blue accents
- compact typography
- subtle borders/depth
- switch-port visualizations
- professional topology canvas
- dense but readable data tables

Do not copy a real Cisco front panel pixel-for-pixel and do not copy Cisco logos/trademarks.

The Device Detail page should include an original reusable switch-front-panel visualization driven by real interface data retrieved during explicit refresh actions.

Do not invent live status or monitoring information.

## Workflow

For each phase:

1. Read `AGENTS.md`.
2. Read `docs/PLAN.md`.
3. Read `docs/architecture.md` if it exists.
4. Read the current `prompts/phase-XX-*.md`.
5. Inspect the current repository before editing.
6. Implement only the requested phase.
7. Run relevant tests.
8. Update documentation affected by the phase.
9. Summarize what changed and list any remaining issues.
10. Do not automatically continue to the next phase.

## Open-Source Release Architecture

Production uses:
- `web`: unprivileged Nginx + React static build
- `api`: FastAPI + network automation
- `postgres`: PostgreSQL

Only `web` may expose a host port by default.
`api` and `postgres` remain container-internal.
Do not mount the entire host `~/.ssh` directory. Mount only the dedicated NMS
private key read-only.
Prefer non-root containers, `no-new-privileges`, dropped capabilities, and the
default Docker seccomp profile where compatible.
Keep dependency versions reproducible and commit lockfiles.
