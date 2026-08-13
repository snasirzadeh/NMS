# Phase 08: Configuration Backups

## Contract

On an explicit user action, execute `show running-config`, store exact text,
SHA-256 checksum, device ID, and timestamp. Provide backup history/details and
a readable monospaced viewer. Do not schedule backups or add workers.

## Outcome

`ConfigBackup`, migration `0004`, repository/service/API, device backup UI, and
checksum/persistence tests were delivered.
