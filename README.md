# Cisco NMS

A local-first, single-user Network Management System for Cisco IOS and IOS-XE
switches. It manages inventory, encrypted SSH credentials, explicit network
operations, topology discovery, configuration previews, and manual backups. It
is not a continuous monitoring platform.

This independent project is not affiliated with or endorsed by Cisco Systems,
Inc.

## Requirements and startup

- Docker Engine with Docker Compose
- Python 3.12+ and Node.js 20+ only for host-side development checks

```bash
cp .env.example .env
# Replace the PostgreSQL and confirmation-secret placeholders.
docker compose up -d --build
```

Open <http://127.0.0.1:8080>. Only `web` publishes a host port; `api` and
`postgres` remain internal. The API applies Alembic migrations at startup. It
does not need access to host SSH files or an SSH agent.

## First-run setup and login

When no administrator exists, the browser displays the setup wizard. Create
the single administrator with a unique password of at least 12 characters that
includes upper-case, lower-case, and numeric characters.

The login password is stored only as an encoded Argon2id hash. A separate
Argon2id derivation uses the password to unwrap a random vault master key. The
vault starts locked after every API restart and is unlocked only by successful
login. Sessions use server-side records, HttpOnly SameSite cookies, and CSRF
protection; the frontend does not use local storage for authentication.

There is no insecure password reset. If the administrator password is lost,
the encrypted credentials cannot be recovered.

## SSH credentials

Open **Credentials** and add a name, Cisco username, private key (paste or
upload), and optional passphrase. The backend validates the key in memory,
extracts safe metadata, encrypts key material with AES-256-GCM, and stores only
ciphertext in PostgreSQL.

After saving, a private key is never returned or displayed. There is no reveal,
copy, download, or private-key API. **Replace Key** writes newly encrypted
material. A credential cannot be deleted while devices reference it.

## Devices, compatibility, and host keys

Create a group, then add a device with management IP, SSH port, stored
credential, platform, and compatibility profile:

- **Modern** uses maintained library defaults.
- **Cisco Legacy** enables device-scoped compatibility for older Cisco SSH
  implementations and displays a warning. Weak algorithms are not global.

The first connection to a device is blocked until its presented SSH host key
fingerprint is explicitly trusted. Later connections compare the stored
fingerprint. If the host key changes, the connection is blocked and the trusted
value is never overwritten automatically.

Device status means only the latest explicit SSH operation:

- green: latest explicit test succeeded
- red: latest explicit test failed
- gray: never tested

The application does not continuously monitor devices.

## Explicit operations

- **Test SSH Connection** connects once and persists a sanitized result.
- **Refresh device** explicitly retrieves facts, interfaces, VLANs, and
  CDP/LLDP neighbors.
- **CLI** permits only the documented show-command allowlist.
- **Topology** runs CDP/LLDP discovery only when requested.
- **Backups** captures running configuration only when requested.
- Configuration apply remains an explicit preview/confirmation workflow.

## Password change

Settings requires the current password. The backend verifies it, unwraps the
vault master key with the old KEK, derives a new KEK, rewraps the same master
key, and creates a new Argon2id login hash. Stored SSH credentials are not
decrypted and re-encrypted individually.

## Development checks

```bash
./local/setup-local.sh
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/pytest -q -o cache_dir=/tmp/nms-pytest-cache
(cd frontend && npm run build)
docker compose config --quiet
```

See [docs/architecture.md](docs/architecture.md) and
[docs/security.md](docs/security.md) for design and security details.

## Stop and backup

```bash
docker compose down
docker compose exec -T postgres pg_dump -U nms -d nms --format=custom > nms.dump
```

Use `docker compose down -v` only when intentionally deleting local database
data.

## License

MIT. See [LICENSE](LICENSE).
