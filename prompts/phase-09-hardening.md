# Phase 9 — Hardening

Implement Phase 9 only.

Perform a security and reliability review.

Review and improve:
- SSH config validation
- IdentityFile allowlist
- path normalization
- symlink handling
- private-key mounts
- filesystem permissions
- secrets/log redaction
- API validation
- error sanitization
- PostgreSQL exposure
- CORS/reverse-proxy configuration
- configuration command validation
- topology input normalization
- destructive-action confirmation
- database indexes/constraints
- transaction handling
- timeout behavior

Add regression tests for discovered issues.

Do not add monitoring.
Do not add unrelated infrastructure.

Create `docs/security.md` documenting the threat model and important operational precautions.

Stop after Phase 9.
