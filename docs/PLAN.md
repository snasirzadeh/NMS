# Local Cisco NMS — Master Plan

## Goal

Build a local single-user Network Management System for Cisco switches.

The application should start with:

```bash
docker compose up -d
```

and stop with:

```bash
docker compose down
```

## Primary Features

- Hierarchical groups
- Device inventory
- Per-device OpenSSH configuration
- SSH public-key authentication
- Test SSH connection
- Device facts
- Interfaces
- VLANs
- CDP/LLDP neighbors
- Safe show-command execution
- Safe configuration workflow with preview and confirmation
- Manual running-config backups
- Per-group topology discovery
- Original Cisco-inspired switch/front-panel UI

## Out of Scope

No monitoring in the initial project:
- SNMP polling
- alerts
- Prometheus/Grafana
- bandwidth graphs
- NetFlow
- syslog
- scheduled polling
- background workers

## SSH Model

Private keys stay outside the repository and database.

Recommended host setup:

```text
~/.ssh/keys/cisco
```

Docker maps the host SSH key directory read-only:

```text
Host:      ${SSH_KEYS_HOST_DIR}
Container: /run/ssh-keys
```

If a saved OpenSSH config contains:

```text
IdentityFile ~/.ssh/keys/cisco
```

the backend must safely map it to:

```text
/run/ssh-keys/cisco
```

using an explicitly configured host-prefix-to-container-prefix rule.

## Main Entities

### Group

- id
- parent_id nullable
- name
- description
- created_at
- updated_at

Groups may be nested to represent the inventory tree, for example:

```text
Aria
├── Main Office
├── Factory
│   ├── Production
│   └── Office
└── Personal Lab
```

### Device

- id
- group_id
- display_name
- hostname
- management_ip
- device_type
- platform
- ssh_port
- ssh_config
- description
- site
- rack
- serial_number
- model
- software_version
- uptime_text
- created_at
- updated_at

### TopologyLink

- id
- group_id
- source_device_id
- source_interface
- destination_device_id nullable
- destination_hostname
- destination_interface
- discovery_protocol
- last_discovered_at

### ConfigBackup

- id
- device_id
- configuration
- checksum
- created_at

### ConfigAudit

- id
- device_id
- commands
- success
- error_summary nullable
- created_at

## Architecture Principles

```text
Frontend
   |
REST API
   |
FastAPI routes
   |
Services
   |---- DeviceService
   |---- SSHConfigService
   |---- CiscoConnectionService
   |---- TopologyService
   |---- BackupService
   |
Repositories / SQLAlchemy
   |
PostgreSQL
```

Raw Netmiko or SSH logic must not live in API route handlers.

## Frontend Direction

Main navigation:

- Dashboard
- Groups
- Devices
- Topology
- Backups

Device Detail tabs:

- Overview
- Interfaces
- VLANs
- Neighbors
- Configuration
- CLI
- Backups

The Device Detail page should include a reusable original `SwitchFrontPanel` component that visually resembles enterprise network hardware without copying a specific Cisco device.

Port state must come from the latest explicit device refresh. If it has not been fetched, show neutral/unknown state.

## Phases

1. Architecture
2. Foundation
3. Groups and Devices
4. SSH Configuration and Key Security
5. Cisco Connectivity
6. Device Management and Cisco-Inspired UI
7. Topology
8. Configuration Backups
9. Hardening
10. Documentation and Release Readiness

Each phase has a dedicated prompt in `prompts/`.

## Open-Source Production Deployment

The release architecture uses three intentionally small services:

- `web`: unprivileged Nginx serving the React build and proxying `/api`
- `api`: FastAPI/Netmiko application with no host-exposed port
- `postgres`: PostgreSQL on an internal Docker network with no host-exposed port

Only `web` binds to the host, on `127.0.0.1:8080` by default.

The API receives only the dedicated NMS SSH private key as a read-only mount.
Do not mount the user's entire `~/.ssh` directory.
