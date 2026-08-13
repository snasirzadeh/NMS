# Phase 04: SSH Security

## Contract

Parse bounded per-device OpenSSH blocks as data. Support Host, HostName, User,
Port, IdentityFile, IdentitiesOnly, and approved legacy algorithm directives.
Reject malformed/ambiguous config, traversal, disallowed paths, and missing
keys at connection time. Never shell-execute config or expose key contents.

## Outcome

The SSH parser, safe host-to-container mapping, effective preview, legacy
warnings, and security regression tests were implemented.
