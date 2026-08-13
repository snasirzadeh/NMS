# Phase 09: Hardening

## Contract

Review SSH validation, allowlists, path/symlink handling, mounts, permissions,
secrets, API validation, error sanitization, PostgreSQL exposure, proxy
headers, configuration confirmation, topology normalization, constraints,
transactions, and timeouts. Add regression tests and a threat model.

## Outcome

The runtime was hardened with required secrets, read-only API filesystem,
security headers, stricter validation, device-bound confirmation tokens,
symlink tests, and `docs/security.md`.
