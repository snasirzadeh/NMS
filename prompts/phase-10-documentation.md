# Phase 10 — Documentation and Release Readiness

Implement Phase 10 only.

Complete the project documentation.

README must cover:
- requirements
- clone/setup
- `.env`
- PostgreSQL
- SSH key location
- SSH key permissions
- Docker key mount
- host-to-container IdentityFile mapping
- first startup
- creating a company
- adding a device
- sample OpenSSH device config
- testing SSH
- refreshing device data
- using Interfaces/VLANs/Neighbors
- safe show commands
- safe configuration workflow
- topology discovery
- manual configuration backup
- stopping the stack
- updating the application
- backing up/restoring PostgreSQL
- troubleshooting common SSH errors

Use this sample config in documentation:

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

Perform a final build/test pass.

Ensure:
- `docker compose up -d` works
- no private keys are committed
- no secrets appear in docs/examples
- PostgreSQL remains internal
- UI build passes
- backend tests pass

Create `docs/release-checklist.md`.

Do not add new major features in this phase.
