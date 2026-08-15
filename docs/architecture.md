# Cisco NMS Architecture

Status: Phase 11 maintained target architecture.

## Boundaries and runtime

```text
                         Browser
                            │
                            ▼
                           Web
                            │
                            ▼
                         FastAPI
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           Auth        VaultService    DeviceService
             │              │              │
             └──────────────┴──────────────▼
                                      SSHTransport
                                           │
                                           ▼
                                         Cisco
                            │
                            ▼
                        PostgreSQL
```

`web` is the only host-published service. `api` and `postgres` are internal
Docker services. The API performs SSH only for an explicit request. There is
no scheduler, polling worker, monitoring stack, Redis, Celery, or SSH-agent
integration.

## Backend ownership

```text
backend/app/
  api/                 authenticated HTTP routers and dependency wiring
  core/                settings, logging, session/security helpers
  models/              SQLAlchemy entities
  schemas/             dedicated request/response models
  services/
    auth/              setup, login, logout, server-side sessions
    vault/             envelope encryption and in-memory unlock state
    credentials/       in-memory key validation and encrypted persistence
    cisco/             SSHTransport, Cisco operations, parsers
    devices/           inventory and explicit status updates
    topology/          explicit discovery
    backups/           manual backups
```

Routes validate input, call one service, and return a dedicated schema. ORM
objects are never serialized blindly. Network and cryptographic operations do
not live in route handlers.

## Authentication and vault design

```text
Admin password
      │
      ├── Argon2id + password salt ──────► login hash in PostgreSQL
      │
      └── Argon2id KDF + separate salt
                         │
                         ▼
                        KEK
                         │ AES-256-GCM
                         ▼
                 wrapped Vault Master Key
                         │
                         ▼
                   AES-256-GCM
                         │
                         ▼
                 encrypted SSH credentials
```

The setup transaction creates exactly one administrator and one vault record.
The password hash includes Argon2id parameters and salt. Vault metadata stores
only the wrapped random 256-bit master key, wrapping nonce, KDF salt, and KDF
parameters. The derived KEK and plaintext master key exist only in backend
memory. Password rotation unwraps and rewraps the same master key and creates a
new login hash. Lost passwords are not recoverable.

Sessions are opaque random values held in HttpOnly, SameSite cookies. Only
token hashes are persisted. Mutating authenticated requests require a CSRF
header derived from the server-side session. Tokens are never stored in
browser local storage.

## Database schema

`admins`, `vaults`, and `auth_sessions` own administrator authentication.
`ssh_credentials` stores username and safe metadata in cleartext and private
key/passphrase ciphertext plus fresh nonces. `devices.ssh_credential_id` is a
restrictive foreign key. Devices also store `ssh_profile`, trusted host-key
fingerprint/algorithm, and `last_connection_status`,
`last_connection_test_at`, and `last_connection_error_code`.

The Phase 11 migration drops the obsolete `devices.ssh_config` column. Existing
devices remain, but their credential reference is null and must be assigned by
the administrator; no old filesystem path is migrated into the new system.

## Credential lifecycle

The Credentials page accepts a private key upload or paste and an optional
passphrase over the authenticated same-origin API. The backend validates the
key in memory, extracts key type/size and SHA256 fingerprint, then encrypts it
under the unlocked vault key. It returns only metadata. Saved keys cannot be
revealed or copied; replacement overwrites ciphertext after validation.

Deletion is rejected while a device references the credential. Device API
responses contain only credential metadata and usage count, never encrypted
payloads or passphrases.

## SSH transport and host keys

`SSHTransport` uses Netmiko for Cisco IOS session preparation and Paramiko's
in-memory key support. It receives management IP, port, username, decrypted
key, optional passphrase, device platform, and profile. It sets
`allow_agent=False`, disables key-file discovery, and never invokes a shell.
The Modern profile uses secure library defaults. Cisco Legacy applies only
device-scoped `diffie-hellman-group14-sha1` and `ssh-rsa` compatibility where
needed.

The transport probes the presented host key before authentication, calculates
its SHA256 fingerprint, and compares it with the stored device fingerprint.
Unknown keys produce a sanitized trust-required result. Changed keys produce a
host-key-changed failure and block the connection. An explicit trust action
must confirm the current fingerprint before persistence.

## Explicit status

Status is based on the most recent explicit SSH operation, not reachability and
not continuous monitoring. `unknown` is gray, `success` is green, and `failed`
is red. Failure persistence stores only a bounded category such as
`authentication_failed`, `connection_timeout`, `host_key_error`, or
`algorithm_negotiation_failed`; stack traces and sensitive exception text are
never returned.

## Testing

Tests cover setup atomicity and one-time behavior, Argon2id hashing, vault
unlock/rotation, randomized AES-GCM nonces, credential redaction and deletion
guards, mocked transport outcomes, host-key trust/change behavior, profile
selection, and every status transition. No test requires physical Cisco
hardware.
