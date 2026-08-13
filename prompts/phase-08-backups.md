# Phase 8 — Configuration Backups

Implement Phase 8 only.

Add manual running-configuration backups.

Workflow:
- user opens a managed device
- clicks Backup Running Configuration
- backend executes `show running-config`
- backend stores configuration, checksum, device ID, timestamp

Frontend:
- device backup history
- backup details
- readable monospaced config viewer

Backend:
- ConfigBackup model
- migration
- service
- repository
- REST endpoints
- checksum generation

Do not schedule backups.
Do not add background workers.

Design the storage so configuration diffing can be added later, but do not implement diffing unless trivial and explicitly allowed by architecture.

Add tests.

Stop after Phase 8.
