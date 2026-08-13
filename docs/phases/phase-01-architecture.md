# Phase 01: Architecture

## Contract

Design the local Cisco NMS architecture before feature implementation. Define
the backend/frontend layers, PostgreSQL entities, REST boundaries, SSH config
parsing and safe host-prefix to `/run/ssh-keys` mapping, Netmiko abstraction,
topology design, Docker networking, logging, errors, testing, and security.

## Outcome

`docs/architecture.md` became the architectural source of truth. The project
uses thin FastAPI routes, service-owned network behavior, SQLAlchemy/Alembic,
React/Vite, an explicit-action model, and internal PostgreSQL networking.
