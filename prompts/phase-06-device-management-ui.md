# Phase 6 — Device Management and Cisco-Inspired UI

Implement Phase 6 only.

Add explicit device refresh actions that retrieve and structure where available:
- hostname
- model
- serial
- IOS/IOS-XE version
- uptime
- inventory
- interfaces
- VLANs
- CDP/LLDP neighbors

Use pyATS/Genie where it clearly improves structured parsing.
Keep fallback parsing isolated and tested.

Build the polished Device Detail experience.

Create reusable frontend components:
- DeviceHeader
- SwitchFrontPanel
- SwitchPort
- InterfaceDetailsDrawer
- StatusIndicator
- TerminalPanel
- ConnectionTestResult

Device tabs:
- Overview
- Interfaces
- VLANs
- Neighbors
- Configuration
- CLI
- Backups

SwitchFrontPanel requirements:
- original enterprise-network-hardware appearance
- inspired by Cisco-style switch interfaces without copying a real model
- dynamic port count
- grouped port spacing
- neutral state when data has not been fetched
- port state based only on latest explicit refresh
- click/hover port details
- interface name
- description
- admin state
- operational state
- VLAN/trunk info
- speed/duplex if known
- neighbor if known

Do not add monitoring or periodic refresh.

Implement safe configuration workflow scaffolding:
- enter commands
- preview
- confirmation
- apply
- audit result

Configuration commands must not execute from the initial form submission.

Add tests for parsing and configuration confirmation behavior.

Stop after Phase 6.
