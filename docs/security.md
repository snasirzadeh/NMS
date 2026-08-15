# Security Model and Operational Precautions

This is a local, single-user network-management tool. Its security boundary is
the browser session, the API process, the encrypted PostgreSQL vault, and
explicit outbound SSH actions.

## Passwords and vault

- The administrator login password is never encrypted or stored reversibly.
  PostgreSQL stores only an encoded Argon2id hash with parameters and salt.
- Vault unlocking uses a separate Argon2id salt/context to derive a KEK, which
  decrypts a random 256-bit vault master key with AES-256-GCM.
- The master key is held only in backend memory and is cleared on lock or
  application shutdown as far as Python memory management permits.
- SSH private keys and optional passphrases are encrypted with fresh AES-GCM
  nonces. Plaintext key material is never written to disk, browser storage, or
  logs.
- Password rotation rewraps the same vault master key. Lost passwords have no
  insecure reset path.

## Sessions and API

- Sessions use opaque random HttpOnly, SameSite cookies; the database stores
  only token hashes.
- Mutating authenticated requests require the server-side session CSRF token.
- Setup is available only while no administrator exists and is protected by an
  atomic single-user initialization transaction.
- Credential response schemas expose metadata only: id, name, username, key
  type/size, fingerprints, timestamps, and usage count.

## SSH and host keys

- The API accepts no host-provided SSH material or agent integration and does
  not invoke arbitrary shell commands.
- Netmiko receives an in-memory Paramiko key object with agent and filesystem
  key discovery disabled.
- Host keys are verified before authentication. Unknown keys require explicit
  trust; changed keys are blocked and never auto-overwritten.
- Legacy algorithms are enabled only by a per-device internal compatibility
  profile, never globally.
- Logs may include device identity, action, result, and sanitized failure code,
  but never passwords, hashes, keys, passphrases, KEKs, vault keys, session
  secrets, encrypted payloads, or raw SSH exception objects.

## Runtime and operations

Compose runs only `web`, `api`, and `postgres`; only web publishes a localhost
port and PostgreSQL is internal-only. The API runs unprivileged with dropped
capabilities, no-new-privileges, and a read-only root filesystem.

Configuration backups may contain device secrets and must be protected with
the PostgreSQL volume. Run tests and the frontend build after changes. The
application does not continuously monitor devices: device status is based on
the most recent explicit SSH operation.
