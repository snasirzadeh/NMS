# Cisco NMS Architecture

Status: Phase 6 device management UI and explicit refresh baseline. This document describes the target shape
of the application; implementation is staged by the phase prompts.

## Goals and boundaries

The application is a local, single-user management tool for Cisco IOS and
IOS-XE switches. It stores inventory and the results of explicit operator
actions. It is not a monitoring system: there is no polling loop, scheduler,
alerting, metrics stack, syslog collector, or background worker.

The production topology is deliberately small:

```text
Browser
   |
   | host port 127.0.0.1:8080
   v
web: unprivileged Nginx + React static files
   |
   | internal Docker network, /api proxy
   v
api: FastAPI + SQLAlchemy + Netmiko
   |                 |
   | internal        | outbound SSH, only on explicit actions
   v                 v
postgres        Cisco switches
```

Only `web` exposes a host port by default. The API and database are reachable
through Docker networks only.

## Repository structure

```text
backend/
  app/
    api/                 # versioned routers and dependency wiring
    core/                # settings, logging, error types, security policy
    database/            # engine, session, Base, migrations integration
    models/              # SQLAlchemy ORM models
    schemas/             # Pydantic request and response models
    services/
      backups/           # manual config backup and checksum operations
      cisco/             # device facts, interfaces, VLANs, neighbors, CLI
      devices/           # inventory and explicit refresh orchestration
      ssh/               # OpenSSH parsing and safe path mapping
      topology/          # topology discovery and link persistence
    main.py              # FastAPI application assembly only
  entrypoint.sh          # migrations, then API process in the container
  migrations/            # Alembic environment and version scripts
  tests/                 # unit, API, and integration tests
frontend/
  src/
    api/                 # typed HTTP client and API error handling
    components/          # reusable UI, including SwitchFrontPanel
    features/            # page-level feature modules
    layouts/             # application shell and navigation
    routes/              # route declarations and page components
    types/               # API and domain TypeScript types
    styles/              # tokens and global styles
docs/                    # architecture, plan, security, operations
prompts/                 # phase-specific implementation contracts
compose.yaml             # local production-like runtime
```

The current scaffold may omit directories until their phase begins. New code
should follow this ownership rather than placing network logic in a route or
database code in a React component.

## Backend layering

```text
HTTP request
  -> API router/dependencies
  -> Pydantic validation
  -> application service
  -> repository/SQLAlchemy session and/or network adapter
  -> response schema
```

Routes authenticate the local request context if that is added later, validate
input, call one service method, and translate known domain errors. They do not
open SSH connections, parse CLI output, or construct SQL queries beyond normal
repository calls.

Services own use cases and transaction boundaries. Repositories, where useful,
hide repeated SQLAlchemy queries. The Cisco service depends on a connection
protocol, not directly on FastAPI. The SSH service parses configuration as
data, never by passing it to a shell.

Settings are loaded from environment variables through `pydantic-settings`.
Secrets are represented by paths or opaque configuration values, never by
private-key contents.

## Database schema

PostgreSQL is the production database. SQLAlchemy 2 ORM models and Alembic
migrations are the source of schema changes.

```text
Group 1 --- * child Group
  |
  +--- * Device 1 --- * ConfigBackup
                     |
                     +--- * ConfigAudit
```

### Group

`id`, `parent_id` nullable, `name`, `description`, `created_at`, and
`updated_at`. A group can contain child groups, allowing structures such as
`Aria / Factory / Production`. Names are not globally unique because the same
site label may appear under different parent groups.

### Device

`id`, `group_id`, `display_name`, `hostname`, `management_ip`, `device_type`,
`platform`, `ssh_port`, `ssh_config`, `description`, `site`, `rack`,
`serial_number`, `model`, `software_version`, `uptime_text`, `created_at`, and
`updated_at`.

`ssh_config` is a device-provided OpenSSH configuration block and is treated as
untrusted text. It does not contain a private key. Device identity and
connection metadata are inventory, not live status.

### TopologyLink

`id`, `group_id`, `source_device_id`, `source_interface`,
`destination_device_id` nullable, `destination_hostname`,
`destination_interface`, `discovery_protocol`, and `last_discovered_at`.

Unknown neighbors remain representable by hostname without inventing a Device
record. Discovery replaces or upserts links for an explicit discovery action;
it does not run periodically.

### ConfigBackup

`id`, `device_id`, `configuration`, `checksum`, and `created_at`. Configuration
is captured only after an explicit backup request. The checksum is generated by
the backend and is useful for display and duplicate detection.

### ConfigAudit

`id`, `device_id`, `commands`, `success`, `error_summary` nullable, and
`created_at`. Store the approved command set and sanitized outcome, never
credentials, private keys, or raw exception objects.

Foreign keys use restrictive delete behavior unless a later phase specifies a
safe cascade. All timestamps are UTC and database-generated or assigned by a
single backend clock policy.

## REST API

The API is versioned under `/api/v1`. Responses use Pydantic schemas and return
stable domain errors with a request identifier. The initial health endpoint may
remain `/health` for container probes.

| Resource | Endpoints | Purpose |
| --- | --- | --- |
| Groups | `GET/POST /groups`, `GET/PATCH/DELETE /groups/{id}`, `GET /groups/tree` | Manage hierarchical inventory groups |
| Devices | `GET/POST /devices`, `GET/PATCH/DELETE /devices/{id}` | Manage switch inventory |
| Device actions | `POST /devices/{id}/refresh`, `/test-connection`, `/show` | Explicit network actions |
| SSH configuration | `POST /devices/ssh-config/preview`, `POST /devices/{id}/ssh-config/preview` | Parse and preview safe effective settings |
| Cisco actions | `POST /devices/{id}/test-connection`, `POST /devices/{id}/show` | Explicit Netmiko actions using an allowlist |
| Device data | `GET /devices/{id}/interfaces`, `/vlans`, `/neighbors` | Read last fetched results |
| Config | `POST /devices/{id}/config/preview`, `/config/apply` | Preview and confirmed configuration workflow |
| Backups | `GET/POST /devices/{id}/backups`, `GET /backups/{id}` | Manual running-config backups |
| Topology | `GET /groups/{id}/topology`, `POST /groups/{id}/topology/discover` | Read or explicitly discover links |

Destructive or network-changing operations require an explicit action request;
the apply endpoint requires a confirmation token produced by preview. Safe
show commands are allowlisted by the Cisco service and are not arbitrary shell
input. Pagination, filtering, and response envelopes should be added with the
resource implementation rather than leaking ORM models to clients.

## OpenSSH configuration and key mapping

The SSH service uses Paramiko's structured OpenSSH parser plus a raw-directive
validation pass. It
does not invoke `ssh`, `ssh-config`, a shell, or string interpolation. Parsing
is performed with a bounded input size and rejects malformed or ambiguous
configuration where security-relevant behavior cannot be determined.

Supported directives are deliberately narrow: host selection, `HostName`,
`User`, `Port`, `IdentityFile`, `IdentitiesOnly`, and explicitly approved
algorithm options such as the legacy options in the project prompt. Unknown
directives are ignored only when they cannot change the connection security;
otherwise they are rejected. No `Match` or include expansion is accepted in a
device block during the first implementation.

IdentityFile mapping is deterministic:

1. Resolve `~` only against the configured allowed host prefix, never against
   the container process user's home directory.
2. Normalize the path and reject NUL bytes, traversal, relative paths outside
   the prefix, and multiple ambiguous identity files.
3. Require the normalized host path to be within the configured
   `SSH_IDENTITY_HOST_PREFIX` (for example `~/.ssh/keys`).
4. Replace that exact prefix with `SSH_IDENTITY_CONTAINER_PREFIX` (for example
   `/run/ssh-keys`) while preserving the relative filename.
5. Resolve the resulting container path and require it to remain inside the
   container prefix. Verify it is a regular readable file when a connection is
   attempted.

For example, `~/.ssh/keys/cisco` maps to
`/run/ssh-keys/cisco`, while `~/.ssh/other`, `/etc/passwd`, and
`~/.ssh/keys/../other` are rejected. The host prefix and container prefix must
be absolute, configured, and normalized. The API never returns the mapped
private-key path or private-key contents to the browser; logs contain only a
stable redacted reason.

The compose mount should expose only the dedicated NMS key directory as
read-only at `/run/ssh-keys`. It must not mount the host's entire `~/.ssh`.

## Cisco connection abstraction

`CiscoConnectionService` is a mockable adapter boundary with `connect`,
`test_connection`, allowlisted `show`, and explicit `refresh` operations. Refresh
uses one session and bounded commands, then passes raw output to isolated fallback
parsers for facts, interfaces, VLANs, and CDP/LLDP neighbors. Its Netmiko factory
receives only the validated effective hostname, user, port, and mapped key path
from the SSH service. It owns timeouts, authentication setup, output
collection, sanitized exception translation, and reliable cleanup. Legacy
algorithm directives are validated and retained in the effective SSH preview;
transport-specific compatibility handling remains inside this adapter boundary.

The Cisco service parses returned output into typed internal results for facts,
interfaces, VLANs, and CDP/LLDP neighbors. Raw output is retained only when a
specific feature needs it and must be redacted before persistence or response.
pyATS/Genie is optional and belongs behind parser adapters for outputs where it
improves correctness. It is not required for basic connectivity and must not
become a second connection lifecycle or a route dependency.

All network work is synchronous at first and runs as an explicit request. A
later implementation may use FastAPI background execution for a single request
only, but no scheduler or persistent worker is part of this architecture.

## Topology discovery

`TopologyService` asks `CiscoConnection` for CDP/LLDP data, normalizes device
and interface identifiers, resolves known devices within the same group tree,
and upserts `TopologyLink` rows. It records the discovery protocol and
timestamp. Ambiguous or unresolved peers are kept as external hostname links.

The topology API returns nodes derived from group devices and links derived
from persisted discovery results. Cytoscape.js or a comparable graph library
is a frontend rendering detail; graph layout must not alter persisted data.

## Frontend structure and state

React and TypeScript use the API client as the only network boundary. Pages are
organized around Dashboard, Groups, Devices, Topology, and Backups. Device
Detail has Overview, Interfaces, VLANs, Neighbors, Configuration, CLI, and
Backups tabs.

`SwitchFrontPanel` is a reusable presentational component. It receives typed
interface data and renders a switch-inspired panel, port labels, and neutral
unknown states. It must not infer live state from CSS, timers, or placeholder
values. A port becomes active/connected/error only from the latest successful
explicit refresh response.

Private-key content is never held in frontend state. Forms send SSH config
text only where the API allows it, and API errors are displayed from sanitized
messages.

## Docker networking and runtime security

Compose defines `web`, `api`, and `postgres` on separate or shared internal
networks as needed. `web` proxies `/api` to `api`; browsers do not connect to
the API or PostgreSQL directly. PostgreSQL has a named volume and no published
port. The API has no published port.

The API receives the dedicated key directory through a read-only bind mount.
Containers use `no-new-privileges`; web and API drop capabilities and use the
default seccomp profile where compatible. Images should run as unprivileged
users, use reproducible dependency lockfiles, and avoid adding tools that are
not needed at runtime.

## Error handling and logging

Domain errors are classified as validation, not-found, conflict, connection,
parse, authorization/policy, and internal errors. The API maps these to stable
HTTP status codes and a generic safe message plus request ID. Netmiko,
Paramiko, filesystem, and database exception details are logged server-side in
sanitized form only; credential material, private-key content, full SSH
configuration where it may contain secrets, and raw device output are never
logged by default.

Logs are structured and include operation, device ID, group ID where
available, duration, result, and request ID. Connection failures expose useful
operator guidance without echoing host configuration or library tracebacks.

## Testing strategy

Phase 2 establishes the test harness and migration checks. Later phases add:

- unit tests for SSH parsing, prefix mapping, traversal rejection, and error
  sanitization;
- service tests using fake `CiscoConnection` implementations, including cleanup
  and timeout failures;
- parser fixtures for IOS/IOS-XE facts, interfaces, VLANs, and CDP/LLDP;
- API tests for validation, ownership relationships, safe command allowlists,
  preview/confirmation behavior, and response schemas;
- migration tests against PostgreSQL for constraints and relationships;
- frontend type/build tests plus focused component tests for unknown and
  refreshed port states;
- Compose smoke tests verifying service reachability and that only `web` is
  host-published.

Phase 5 adds fake-session tests for explicit connection, safe show commands,
disconnect cleanup, and sanitized network failures. No test requires Cisco
hardware.

Tests must use generated fixtures and temporary keys, never a real private key
or production device. Network integration tests are opt-in and require an
explicit environment flag.

## Major trade-offs

- PostgreSQL is retained even for single-user local use because the domain has
  relationships, migration requirements, and durable configuration history.
- Explicit synchronous actions keep behavior understandable and honor the
  no-monitoring scope, at the cost of a request waiting for a slow switch.
- A narrow SSH directive allowlist is safer and easier to test than supporting
  the full OpenSSH grammar, at the cost of rejecting unusual configurations.
- Netmiko is the primary adapter because it is mature for Cisco CLI workflows;
  pyATS/Genie is optional per parser and adds dependency weight only where it
  materially improves parsing.
- Unknown topology peers are stored as links rather than auto-created devices,
  avoiding false inventory while preserving discovery information.

## Phase 5 acceptance criteria

Phase 5 is complete when:

1. The FastAPI app has settings, database engine/session wiring, and a health
   route that remains usable without a live Cisco device.
2. Netmiko is behind a mockable connection service with timeout, authentication,
   negotiation, and sanitized error handling.
3. Test Connection performs one explicit connect/disconnect and returns the
   latest request result without introducing polling or background workers.
4. Show commands are limited to the documented safe allowlist and never invoke
   a local shell or arbitrary configuration command.
5. The backend test command covers fake sessions, cleanup, allowlisting, and
   sanitized failures without real Cisco hardware.
6. The frontend exposes Test Connection results and retains SSH preview and
   legacy algorithm warnings.
