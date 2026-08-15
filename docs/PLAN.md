# Local Cisco NMS — Master Plan

## Goal

Build a local, single-user Network Management System for Cisco switches. The
application stores inventory and explicit operator results; it is not a
continuous monitoring system.

## Primary features

- Hierarchical groups and device inventory
- First-run administrator setup and authenticated sessions
- Encrypted SSH credential vault with credential replacement/deletion
- Device-scoped Modern and Cisco Legacy SSH compatibility profiles
- Database-backed SSH host-key verification
- Explicit SSH connection tests with unknown/success/failed status
- Device facts, interfaces, VLANs, neighbors, safe show commands, topology,
  configuration previews, and manual backups

## Authentication and vault

The setup wizard creates one administrator and initializes the vault in one
transaction. The administrator password is stored only as an encoded Argon2id
password hash. Vault unlocking derives a separate Argon2id KEK, unwraps a
random 256-bit vault master key with AES-256-GCM, and keeps the master key only
in backend memory. SSH private keys and optional passphrases are encrypted with
AES-256-GCM under that master key before being stored in PostgreSQL.

The browser never receives password hashes, vault keys, encrypted credential
blobs, or plaintext private keys. A restart starts with the vault locked.

## Main entities

### Device

`id`, `group_id`, `display_name`, `hostname`, `management_ip`, `device_type`,
`platform`, `ssh_port`, `ssh_credential_id`, `ssh_profile`, descriptive and
Cisco fact fields, trusted host-key metadata, and latest explicit connection
status fields.

### SSH credential

`id`, `name`, `username`, encrypted private key and passphrase blobs/nonces,
key type/size, SHA256 fingerprint, and timestamps. Encrypted fields are never
part of API response schemas.

### Other entities

Groups, topology links, configuration backups, and configuration audits retain
their existing ownership and restrictive-delete behavior.

## SSH behavior

Users select a stored credential and an internal SSH profile on each device.
They do not paste OpenSSH configuration and the API never reads a private-key
path or an SSH agent. Netmiko remains behind `SSHTransport` because it provides
the maintained Cisco IOS session behavior and accepts an in-memory Paramiko
key object. The Modern profile uses library defaults; Cisco Legacy enables only
the explicitly scoped legacy algorithms needed for that device.

Before authentication, the transport obtains the server host key and checks
its SHA256 fingerprint against the device record. Unknown keys are rejected
until explicitly trusted. Changed keys are blocked and are never overwritten
automatically.

## Status semantics

`unknown`, `success`, and `failed` describe the latest explicit SSH operation.
Green means the latest explicit connection test succeeded, red means it
failed, and gray means it has never been tested. There are no polling workers,
schedulers, Redis, Celery, or background monitoring services.

## Runtime

Compose contains only `web`, `api`, and `postgres`. Only web is host-accessible;
API and PostgreSQL remain internal. The API has no host SSH mounts and all
credential material is self-contained in the encrypted PostgreSQL vault.
