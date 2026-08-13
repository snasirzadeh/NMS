# Cisco NMS

A local-first, open-source network management system for Cisco IOS and IOS-XE
switches. The project focuses on inventory, SSH-based management, topology,
configuration workflows, and configuration backups. Monitoring is intentionally
out of scope for the initial release.

> This is an independent open-source project and is not affiliated with or
> endorsed by Cisco Systems, Inc.

## Architecture

```text
Browser
  |
  v
web (unprivileged Nginx + React)
  |
  +-- /api --> api (FastAPI + Netmiko)
                  |
                  +--> PostgreSQL
                  |
                  +--> SSH --> network devices
```

Only the `web` service is exposed to the host. PostgreSQL is on an internal
Docker network, and the API receives a dedicated SSH private key through a
read-only bind mount.

## Development Status

This repository is a Codex-ready starter scaffold. The application is intended
to be implemented incrementally using the prompts in `prompts/`.

## Local Setup

See [local/README.md](local/README.md) for the recorded local setup state,
cleanup commands, and the reproducible setup script.

```bash
cp .env.example .env
```

Edit `.env`, replace both placeholder secrets, and set `NMS_SSH_KEYS_HOST_DIR`
to the absolute host directory containing the dedicated NMS key.

Example:

```text
NMS_SSH_KEYS_HOST_DIR=/home/alice/.ssh/keys
```

Use restrictive permissions:

```bash
chmod 600 ~/.ssh/keys/cisco-nms
```

Never copy private keys into this repository.

## Codex

Start with:

```text
Read AGENTS.md, docs/PLAN.md, and prompts/phase-01-architecture.md.

Inspect the repository.
Implement Phase 1 only.
Do not begin Phase 2.
```

Review each phase before continuing.

## Target Runtime

When implementation is complete:

```bash
docker compose up -d
```

Open:

```text
http://127.0.0.1:8080
```

Stop with:

```bash
docker compose down
```

## License

MIT. See `LICENSE`.
