# Cisco NMS

A local-first network management system for Cisco IOS and IOS-XE switches.
It manages inventory, explicit SSH actions, device refresh data, group-scoped
topology discovery, safe configuration previews, and manual running-config
backups. It is not a monitoring platform.

This independent project is not affiliated with or endorsed by Cisco Systems,
Inc.

## Requirements

- Linux or another Docker-compatible host
- Python 3.12 or newer for local backend tests
- Node.js 20 or newer and npm for the frontend build
- Docker Engine with Docker Compose
- A dedicated Cisco SSH public/private key pair outside this repository

PostgreSQL is provided by Compose. Do not install or expose PostgreSQL on the
host for this application.

## Clone and Setup

```bash
git clone <repository-url> nms
cd nms
cp .env.example .env
```

Edit `.env` before starting. Replace `POSTGRES_PASSWORD` and
`NMS_CONFIG_CONFIRMATION_SECRET` with independently generated values. Set
`DATABASE_URL` to use the same PostgreSQL password. Set
`NMS_SSH_KEYS_HOST_DIR` to the absolute host directory containing the
dedicated NMS private key.

Create the project-local development environment when running checks outside
Docker:

```bash
./local/setup-local.sh
backend/.venv/bin/pytest -q
(cd frontend && npm run build)
```

The setup script keeps generated dependencies in `backend/.venv` and
`frontend/node_modules`. See [local/README.md](local/README.md) for removal
commands and the recorded local setup state.

## SSH Keys and Mapping

Keep the private key outside the repository, for example:

```text
/home/alice/.ssh/keys/cisco-nms
```

Restrict the key permissions:

```bash
chmod 750 /home/alice/.ssh/keys
chmod 640 /home/alice/.ssh/keys/cisco-nms
```

Compose mounts only the configured key directory read-only:

```text
host:      ${NMS_SSH_KEYS_HOST_DIR}
container: /run/ssh-keys
```

Set `NMS_SSH_KEYS_GID` to the host group ID that owns this directory. Compose
adds that group to the API container so the unprivileged API process can read
the mounted key without making it world-readable. On Linux, use `id -g`.

The saved device SSH configuration uses the configured host prefix and is
mapped safely to the container prefix. With the defaults, this mapping is:

```text
IdentityFile ~/.ssh/keys/cisco
                 -> /run/ssh-keys/cisco
```

Traversal, unsupported paths, and symlinks resolving outside the mounted key
directory are rejected. The API never stores or returns private-key contents.

## First Startup

Start the application from the repository root:

```bash
docker compose up -d --build
```

Open <http://127.0.0.1:8080>. Verify the proxy and API health endpoints:

```bash
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/api/v1/health
```

Only the unprivileged `web` service publishes a host port. The API and
PostgreSQL services remain container-internal. Compose applies pending
Alembic migrations when the API starts.

## Initial Workflow

1. Open **Groups** and create the top-level group that represents a company or
   operating boundary, such as `Aria`.
2. Add child groups such as `Main Office`, `Factory`, or `Personal Lab`.
3. Open **Devices**, choose a group, and add the switch identity, management IP,
   and SSH configuration.
4. Use **Validate SSH config** before saving a device. The preview shows the
   effective host, port, user, and safe identity-file-relative path.

Use **Edit** beside an existing device to update its metadata or replace its
SSH configuration. Validate the replacement configuration before saving; the
existing device record is updated in place.

Use this sample configuration as a starting shape, replacing only the host
and key values appropriate to your environment:

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

The legacy algorithm lines are accepted for compatibility and shown with
warnings. Prefer modern algorithms on devices that support them.

## Device Operations

Open a managed device from the Devices page.

- **Test SSH** performs one explicit connection test and disconnects.
- **Refresh device** retrieves facts, inventory, interfaces, VLANs, and
  CDP/LLDP neighbors. It does not poll or run in the background.
- **Interfaces**, **VLANs**, and **Neighbors** show the latest successful
  explicit refresh data. The switch front panel remains neutral until a
  refresh returns interface data.
- **CLI** exposes only the safe show-command allowlist, including `show
  version`, `show inventory`, `show interfaces status`, `show ip interface
  brief`, `show vlan brief`, `show cdp neighbors detail`, `show lldp neighbors
  detail`, and `show running-config`.

The **Configuration** tab accepts commands for validation and preview. A
confirmation token is required for the apply step, is time-limited and bound
to the device, and the current apply endpoint records an audit-only result;
configuration commands are not executed in this phase.

## Topology Discovery

Open **Topology**, select a group, and click **Discover topology**. The backend
explicitly retrieves CDP and LLDP data from managed devices in that group tree,
normalizes and deduplicates links, and stores the result. Unknown peers are
shown as **Discovered / Unmanaged** and are never silently added to inventory.
Use the node action to move an unmanaged hostname into the device-inventory
workflow. Pan, zoom, and fit controls affect only the graph view.

## Manual Configuration Backups

Open a managed device, select **Backups**, and click **Backup running
configuration**. The backend executes `show running-config` once, stores the
exact returned text, computes a SHA-256 checksum, and records the timestamp.
Select a history entry to view the monospaced configuration. Backups can
contain sensitive Cisco configuration data; protect the PostgreSQL volume and
host access accordingly. Backups are never scheduled.

## Stop, Update, and Database Backup

Stop the stack without deleting data:

```bash
docker compose down
```

Update the application from a clean working tree:

```bash
git pull --ff-only
docker compose up -d --build
```

Create a PostgreSQL logical backup through the Compose service:

```bash
docker compose exec -T postgres pg_dump \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  > nms-$(date +%Y%m%d-%H%M%S).dump
```

The variables must be available in the shell or replaced with the values from
`.env`. Restore into a stopped or disposable database environment after
creating the target database:

```bash
cat backup.dump | docker compose exec -T postgres \
  sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists'
```

For a destructive local reset only, remove the Compose volume:

```bash
docker compose down -v
```

## Troubleshooting SSH

**SSH authentication failed**: verify the mapped key exists inside the API
container, the host key permissions are restrictive, the Cisco user is
correct, and the device accepts the key. Do not paste private-key contents
into the application.

**SSH device is unreachable**: verify the management IP, route, firewall, and
SSH port from the Docker host. The API container must be able to reach the
device network.

**SSH connection timed out**: confirm the device is listening on the configured
port and that intermediate ACLs permit the connection. The adapter uses bounded
connection, authentication, and banner timeouts.

**SSH negotiation failed**: inspect the preview warnings and device SSH
algorithm support. Legacy compatibility options are accepted only through the
structured SSH configuration parser.

**IdentityFile is outside the configured allowed prefix**: use a path under
`SSH_IDENTITY_HOST_PREFIX`, normally `~/.ssh/keys`, and ensure the resolved
file remains inside the mounted `/run/ssh-keys` directory.

For security boundaries and operational precautions, see
[docs/security.md](docs/security.md). For contribution checks, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Future Development

The original implementation work is complete. For maintenance or new feature
requests, read [`docs/README.md`](docs/README.md) and
[`docs/project-guide/maintenance.md`](docs/project-guide/maintenance.md)
before editing. Product operations remain documented in this README, `docs/`,
and `local/`.

## License

MIT. See [LICENSE](LICENSE).
