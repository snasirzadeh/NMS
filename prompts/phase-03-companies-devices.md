# Phase 3 — Companies and Devices

Read the project instructions and architecture.

Implement Phase 3 only.

Backend:
- Company model/schema/repository/service/routes
- Device model/schema/repository/service/routes
- Alembic migrations
- validation for management IP and SSH port
- company/device ownership validation

Device fields must include:
- company
- display name
- hostname
- management IP
- device type
- platform
- SSH port
- SSH config
- description
- site
- rack
- serial number
- model
- software version
- timestamps

Frontend:
- Companies page
- Company workspace
- Devices inventory page
- Add Device form
- Edit Device form
- Device Details shell
- polished Cisco-inspired visual styling

The Add/Edit Device page must include a large monospaced SSH Configuration textarea, but actual SSH parsing/security behavior belongs to Phase 4.

Do not make real SSH connections yet.

Add tests for CRUD and validation.

Stop after Phase 3.
