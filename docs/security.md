# Security Model and Operational Precautions

This application is a local, single-user management tool. Its main security
boundary is the browser-to-web proxy and the outbound SSH connection from the
API container to managed switches. It is not an internet-facing multi-tenant
service.

## Threat model

The application treats device-provided SSH configuration, CLI output, neighbor
identifiers, and configuration commands as untrusted input. The relevant risks
are command injection, SSH key disclosure, path traversal, unsafe network
errors, accidental configuration changes, and unauthorized access to stored
configuration backups.

## SSH keys and filesystem

- Store private keys outside the repository, preferably in a dedicated host
  directory such as `~/.ssh/keys` with restrictive permissions.
- Compose mounts only that directory read-only at `/run/ssh-keys`; it does not
  mount the host `~/.ssh` directory.
- The API container runs as the unprivileged `nms` user, drops capabilities,
  uses `no-new-privileges`, and has a read-only root filesystem with a
  no-execute temporary directory.
- `IdentityFile` is parsed as data. It must remain within the configured host
  prefix and its resolved container path must remain within the mounted key
  directory. Symlinks resolving outside that directory are rejected.
- Private-key contents are never stored in PostgreSQL, returned by the API, or
  written to logs.

## Network and API boundaries

- Only Nginx publishes a host port, bound to `127.0.0.1` by default.
- PostgreSQL is on the internal Docker network and has no published port.
- Browser API calls use the same-origin `/api/` reverse proxy; no permissive
  CORS policy is enabled.
- Nginx adds framing, content-type, referrer, content-security, and
  permissions-policy headers. Keep the local port behind a trusted host or
  add TLS before exposing it beyond the local machine.
- Replace the PostgreSQL password and configuration confirmation secret in
  `.env`; Compose refuses to start when these required values are absent.

## Explicit actions and secrets

- SSH connections, refreshes, topology discovery, CLI commands, and backups
  happen only in response to an explicit request. There is no scheduler,
  polling loop, or background worker.
- Show commands use an allowlist. Network exceptions are reduced to safe
  categories before reaching the API response.
- Configuration previews are bounded and reject shell/control operators and
  destructive tokens. Confirmation tokens expire and are bound to the device
  for which they were created. The current apply endpoint is audit-only and
  does not execute commands.
- Running configurations are stored only after a manual backup action. Treat
  backup access as sensitive because Cisco configurations may contain secrets.

## Operations checklist

1. Copy `.env.example` to `.env` and replace both placeholder secrets with
   independently generated values.
2. Set `NMS_SSH_KEYS_HOST_DIR` to the dedicated key directory and verify key
   permissions before starting Compose.
3. Keep the web port bound to localhost unless a secured reverse proxy is in
   front of it.
4. Review backup contents and database volume permissions as sensitive data.
5. Use `docker compose down -v` only when intentionally deleting development
   database data.
6. Run backend tests and the frontend build after dependency or container
   changes.
