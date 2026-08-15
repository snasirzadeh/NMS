# Phase 11 refactor report

The pre-refactor audit found the old SSH architecture in:

- `backend/app/services/ssh/config.py` and `keys.py` (OpenSSH parsing,
  `IdentityFile` mapping, and filesystem-backed uploads).
- `Device.ssh_config`, device schemas, Cisco services, backups, topology, and
  tests.
- Settings key-file routes and frontend SSH text/key-file forms.
- Compose bind mounts, group permissions, and host/container key-prefix
  environment variables.
- README, local setup, security, release, phase, and architecture documents.

Phase 11 removes those paths. It introduces a single administrator, Argon2id
password hashing, server-side sessions, an AES-256-GCM envelope-encrypted
credential vault, internal SSH compatibility profiles, database-backed host
key verification, and explicit connection-test status. Existing devices are
preserved by the migration but receive a null credential reference because the
old text configuration cannot be safely converted automatically.

