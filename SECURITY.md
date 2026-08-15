# Security Policy

Please report vulnerabilities privately to the maintainers rather than opening
a public issue containing exploit details or sensitive material.

The maintained security model is documented in
[`docs/security.md`](docs/security.md). Core invariants include Argon2id-only
password storage, envelope-encrypted SSH credentials, server-side sessions,
CSRF protection, strict host-key verification, sanitized errors, no external
key paths or agent integration, and no private-key response API.
