from app.services.topology import NormalizedNeighbor, normalize_hostname, normalize_interface, normalize_neighbors


def test_topology_normalizes_cisco_interface_and_hostname_forms() -> None:
    assert normalize_interface("GigabitEthernet 1/0/1") == "Gi1/0/1"
    assert normalize_interface("TenGigabitEthernet1/0/49") == "Te1/0/49"
    assert normalize_hostname(" Core01.example.com. ") == "core01"


def test_topology_deduplicates_cdp_and_lldp_preferring_cdp() -> None:
    result = normalize_neighbors(
        [
            NormalizedNeighbor("core01.example.com.", "GigabitEthernet1/0/1", "Gi1/0/24", "LLDP"),
            NormalizedNeighbor("core01", "Gi1/0/1", "GigabitEthernet1/0/24", "CDP"),
            NormalizedNeighbor("access02", "Gi1/0/2", "Gi1/0/48", "LLDP"),
        ]
    )

    assert len(result) == 2
    cdp = next(item for item in result if item.local_interface == "Gi1/0/1")
    assert cdp.protocol == "CDP"
