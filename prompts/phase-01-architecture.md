# Phase 1 — Architecture

Read `AGENTS.md` and `docs/PLAN.md` first.

Inspect the repository before making changes.

Your task is Phase 1 only.

Design and document the architecture for the local Cisco NMS.

Cover:

- final repository structure
- backend layering
- frontend structure
- database entities and relationships
- REST API design
- OpenSSH config parsing strategy
- safe IdentityFile path mapping
- Netmiko connection abstraction
- pyATS/Genie usage boundaries
- topology discovery architecture
- Docker Compose networking and key mounts
- logging/error handling
- testing strategy
- security boundaries

Pay special attention to this SSH requirement:

A device can store an SSH config like:

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

The host key directory is mounted read-only into `/run/ssh-keys`.

The architecture must define a safe deterministic mapping from the allowed host prefix (for example `~/.ssh/keys`) to `/run/ssh-keys`.

Do not execute SSH config through shell interpolation.

Deliverables:

1. Replace `docs/architecture.md` with the agreed architecture.
2. Add diagrams in Markdown where useful.
3. Identify major trade-offs.
4. List concrete acceptance criteria for Phase 2.

Do not implement Phase 2 or later features.
