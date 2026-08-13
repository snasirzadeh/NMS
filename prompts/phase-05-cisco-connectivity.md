# Phase 5 — Cisco Connectivity

Read all project instructions and architecture.

Implement Phase 5 only.

Create a `CiscoConnectionService` abstraction around Netmiko.

Responsibilities:
- consume validated effective SSH configuration
- connect with SSH public-key authentication
- support Cisco IOS and IOS-XE
- support the required legacy SSH compatibility options from saved config
- reliable disconnect
- connection timeout handling
- authentication failure handling
- SSH negotiation failure handling
- sanitized exceptions

Implement:
- Test Connection endpoint
- Test Connection UI action
- latest explicit test result display
- safe allowlisted show-command endpoint
- initial quick commands:
  - show version
  - show inventory
  - show interfaces status
  - show ip interface brief
  - show vlan brief
  - show cdp neighbors detail
  - show lldp neighbors detail
  - show running-config

Do not expose local shell execution.
Do not permit arbitrary configuration commands yet.

Network calls must be mockable.

Add tests using mocks/fakes so tests do not require real Cisco hardware.

Stop after Phase 5.
