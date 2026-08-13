# Security Policy

## Reporting a Vulnerability

Please do not disclose suspected vulnerabilities in public issues.

Before the project is published, configure a private security-reporting channel
for the repository and replace this section with the final reporting method.

## Security Model

- SSH private keys are never stored in PostgreSQL.
- The API receives only a read-only mount of the dedicated NMS private key.
- PostgreSQL is isolated on an internal Docker network.
- Only the web service is exposed to the host.
- Application containers should run without unnecessary Linux capabilities.
- Device SSH configuration is treated as untrusted input.
- IdentityFile resolution must use an explicit allowlist and prevent traversal.
- Network errors must be sanitized before being returned to clients.
