# Phase 4 — SSH Configuration and Key Security

Read the full project documentation first.

Implement Phase 4 only.

Build `SSHConfigService`.

It must safely parse and validate per-device OpenSSH config blocks.

Required directives to support initially:
- Host
- HostName
- User
- Port
- IdentityFile
- IdentitiesOnly
- KexAlgorithms
- HostKeyAlgorithms
- PubkeyAcceptedAlgorithms

Requirements:
- preserve legacy Cisco algorithm overrides such as `+diffie-hellman-group14-sha1` and `+ssh-rsa`
- show non-blocking UI warnings for legacy algorithms
- reject malformed or ambiguous config
- reject multiple unrelated Host blocks in the single-device editor unless architecture explicitly supports them safely
- reject IdentityFile path traversal
- reject IdentityFile outside the configured allowed host prefix
- map host prefix safely to `/run/ssh-keys`
- check that the mapped key exists and is a regular file before connection use
- never read/return private-key contents through the API
- never log private-key contents
- never execute the text through shell interpolation

Frontend:
- SSHConfigEditor
- parsed/effective connection preview
- validation errors
- legacy algorithm warning
- IdentityFile mapping preview

Add comprehensive tests for:
- valid config
- invalid config
- path traversal
- disallowed IdentityFile paths
- legacy options
- safe path mapping
- absence of private-key content from responses/logging

Do not connect to Cisco yet.

Stop after Phase 4.
