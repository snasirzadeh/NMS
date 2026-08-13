# Phase 05: Cisco Connectivity

## Contract

Create a mockable Netmiko adapter with reliable disconnect, bounded timeouts,
sanitized authentication/negotiation errors, explicit Test Connection, and an
allowlisted show-command endpoint. Do not expose shell execution or arbitrary
configuration commands.

## Outcome

`CiscoConnectionService` owns connection lifecycle and allowlisted show calls;
fake-session tests cover success, cleanup, errors, and command rejection.
