"""Parser regression tests for observed SonicOS payload quirks."""

from __future__ import annotations

from sonicwall.models.nat_policy import NatPolicy
from sonicwall.models.service_object import ServiceObject


def test_nat_policy_parses_firmware_variant_shape() -> None:
    raw = {
        "ipv4": {
            "name": "Default NAT Policy",
            "inbound": "X0",
            "outbound": "X1",
            "source": {"group": "All Interface IP"},
            "translated_source": {"name": "X1 IP"},
            "destination": {"any": True},
            "translated_destination": {"original": True},
            "service": {"name": "HTTPS Management"},
            "translated_service": {"original": True},
            "enable": True,
        }
    }
    policy = NatPolicy.from_api_response(raw)
    assert policy.inbound_interface == "X0"
    assert policy.outbound_interface == "X1"
    assert policy.original_source == "All Interface IP"
    assert policy.translated_source == "X1 IP"
    assert policy.original_destination == "any"
    assert policy.translated_destination == "original"
    assert policy.original_service == "HTTPS Management"
    assert policy.translated_service == "original"
    assert policy.enabled is True


def test_service_object_allows_long_names_from_device() -> None:
    raw = {
        "service_object": {
            "name": "Version 2 Multicast Listener Report (IPv6)",
            "protocol": {"icmp": {"type": 143, "code": 0}},
        }
    }
    svc = ServiceObject.from_api_response(raw)
    assert svc.name == "Version 2 Multicast Listener Report (IPv6)"
