# Phase 7 — Topology

Implement Phase 7 only.

Topology is per company.

Use managed devices as discovery seeds.

Retrieve neighbor information through explicit user-triggered discovery using:
- CDP
- LLDP

Persist topology links with:
- company
- source device
- source interface
- destination managed device if known
- destination hostname
- destination interface
- discovery protocol
- discovery timestamp

Unknown neighbors:
- do not silently create devices
- render as Discovered / Unmanaged
- provide Add to Inventory action

Frontend:
- professional topology canvas
- Cytoscape.js or architecture-approved equivalent
- pan
- zoom
- fit to screen
- readable interface labels
- click node to open managed device
- distinct but tasteful unmanaged-node treatment
- original enterprise network visual language
- no fake monitoring colors

Avoid social-network graph styling.

Add parser/service tests for CDP/LLDP normalization and deduplication.

Stop after Phase 7.
