from app.services.cisco.parsers import parse_refresh


def test_parse_refresh_structures_facts_interfaces_vlans_and_neighbors() -> None:
    result = parse_refresh(
        {
            "show version": "sw01 uptime is 2 weeks, 3 days\nCisco IOS Software, Version 17.09.04a\ncisco C9300-24T",
            "show inventory": 'NAME: "Chassis", DESCR: "Switch"\nPID: C9300-24T, VID: V01, SN: FOC123',
            "show interfaces status": "Port      Name                 Status       Vlan       Duplex  Speed Type\nGi1/0/1   uplink               connected    trunk      a-full a-1000 10/100/1000",
            "show ip interface brief": "Interface              IP-Address      OK? Method Status                Protocol\nGi1/0/1                unassigned      YES unset  up                    up",
            "show vlan brief": "10   Users                         active",
            "show cdp neighbors detail": "Device ID: core01\nPlatform: cisco C9300, Capabilities: Switch\nInterface: GigabitEthernet1/0/1, Port ID (outgoing port): Gi1/0/24",
            "show lldp neighbors detail": "Local Port id: Gi1/0/2\nSystem Name: access02\nPort id: Gi1/0/48",
        }
    )

    assert result.facts.hostname == "sw01"
    assert result.facts.model == "C9300-24T"
    assert result.facts.serial == "FOC123"
    assert result.facts.software_version == "17.09.04a"
    assert result.interfaces[0].mode == "trunk"
    assert result.interfaces[0].operational_state == "up"
    assert result.vlans[0].vlan_id == 10
    assert {neighbor.protocol for neighbor in result.neighbors} == {"CDP", "LLDP"}


def test_parser_returns_empty_values_for_unrecognized_output() -> None:
    result = parse_refresh({})

    assert result.facts.hostname == ""
    assert result.interfaces == []
    assert result.vlans == []
    assert result.neighbors == []
