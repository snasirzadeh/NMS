# Local Setup Record

This directory contains local-development instructions and scripts. It is
separate from the application runtime and does not contain private keys.

## Recorded local state

The setup script was run from the repository root on 2026-08-13. The local
tool versions observed after setup were:

```text
Python 3.13.5
Node.js v22.23.2
npm 10.9.8
Docker 29.7.2
Docker Compose v5.4.0
```

The setup created or populated these project-local paths:

```text
backend/.venv          Python virtual environment and backend packages
frontend/node_modules  Frontend npm packages
frontend/package-lock.json  npm dependency lockfile
```

The script did not install PostgreSQL on the host. PostgreSQL is provided by
Docker Compose. It also did not create, copy, or store any SSH private key.

The setup script did not install system packages. Python, Node.js, npm, Docker,
and Docker Compose are host-level prerequisites installed separately. On Debian
13, the prerequisite commands used for this project are:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl ca-certificates
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

Docker Engine and its Compose plugin should be installed from Docker's official
Debian instructions. Verify the host tools with:

```bash
python3 --version
node --version
npm --version
docker --version
docker compose version
```

## Repeat setup

From the repository root:

```bash
./local/setup-local.sh
```

The Compose key directory is configured with `NMS_SSH_KEYS_HOST_DIR` in `.env`
and is mounted read-only at `/run/ssh-keys` inside the API container. The
default fallback is the empty `local/ssh-keys` directory for foundation testing;
put real keys outside the repository.
Set `NMS_SSH_KEYS_GID` to the owning host group ID, normally the output of
`id -g`. For a dedicated key directory, use directory mode `750` and key file
mode `640`; the API receives that group as a supplementary read-only group.

If an older `.env` still contains `NMS_SSH_PRIVATE_KEY` or sets
`SSH_IDENTITY_CONTAINER_PREFIX=/run/nms-ssh`, replace those values with the
directory-based settings from `.env.example` before starting Compose.

Start the stack and verify both health paths:

```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/api/v1/health
```

The API waits for PostgreSQL, applies pending Alembic migrations, and then
starts FastAPI.

SSH configuration is validated by the Phase 4 preview endpoint without opening
an SSH connection:

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/devices/ssh-config/preview \
  -H 'Content-Type: application/json' \
  -d '{"config":"Host cisco-sw1\n    HostName 192.0.2.10\n    User cisco\n    IdentityFile ~/.ssh/keys/cisco"}'
```

Phase 5 adds explicit device actions. The Test Connection button calls
`POST /api/v1/devices/{id}/test-connection`; safe show commands call
`POST /api/v1/devices/{id}/show`. The allowlisted commands are `show version`,
`show inventory`, `show interfaces status`, `show ip interface brief`,
`show vlan brief`, `show cdp neighbors detail`, `show lldp neighbors detail`,
and `show running-config`. No arbitrary shell or configuration commands are
accepted.

These actions require a real device key and are intentionally not exercised by
the automated tests. Phase 5 tests use fake Netmiko sessions, so running the
test suite never connects to a switch.

Run local checks:

```bash
backend/.venv/bin/pytest -q
(cd frontend && npm run build)
```

## Remove project-local dependencies

This removes only generated dependencies inside this repository:

```bash
rm -rf backend/.venv frontend/node_modules
```

Keep `frontend/package-lock.json`; it is source-controlled dependency metadata,
not an installed package directory. Remove `.env` separately only if you no
longer need the local configuration:

```bash
rm -f .env
```

## Remove Docker data

Stop containers and remove the Compose-created containers and networks:

```bash
docker compose down
```

To also delete the local PostgreSQL volume and its development data:

```bash
docker compose down -v
```

## Remove host tools

The setup script does not manage host-level uninstallation. On Debian, remove
Node.js with:

```bash
sudo apt remove nodejs
```

Do not remove Python if the operating system depends on it. Docker removal is
system-wide and can delete containers, images, and data; follow Docker's
uninstall procedure and review its data-removal steps before running them.
