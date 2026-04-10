"""Tests for firmware schema-array write fallbacks."""

from __future__ import annotations

import httpx
import pytest

from sonicwall import SonicWallClient
from sonicwall.models.access_rule import AccessRule, AccessRuleAction, RuleAddress, RuleService
from sonicwall.models.nat_policy import NatPolicy
from sonicwall.models.service_object import PortRange, ServiceObject, ServiceProtocol
from tests.conftest import AUTH_SUCCESS_RESPONSE, HOST, PASSWORD, USERNAME


def _schema_err(entity: str) -> dict:
    return {
        "status": {
            "success": False,
            "info": [
                {
                    "level": "error",
                    "code": 400,
                    "message": f"Schema validation error: property '{entity}' expected '['",
                }
            ],
        }
    }


@pytest.mark.asyncio
async def test_service_object_create_schema_fallback(mock_sonicwall) -> None:
    calls = {"count": 0}

    def create_handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(400, json=_schema_err("service_objects"))
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    mock_sonicwall.post("/service-objects").mock(side_effect=create_handler)
    mock_sonicwall.get("/service-objects/name/sdk-svc").mock(
        return_value=httpx.Response(
            200,
            json={
                "service_objects": [
                    {"name": "sdk-svc", "protocol": {"tcp": {"begin": 65000, "end": 65000}}}
                ]
            },
        )
    )

    obj = ServiceObject(
        name="sdk-svc", protocol=ServiceProtocol(tcp=PortRange(begin=65000, end=65000))
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        await client.service_objects.create(obj)
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_nat_policy_create_schema_fallback(mock_sonicwall) -> None:
    calls = {"count": 0}

    def create_handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(400, json=_schema_err("nat_policies"))
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    mock_sonicwall.post("/nat-policies/ipv4").mock(side_effect=create_handler)
    mock_sonicwall.get("/nat-policies/ipv4/name/sdk-nat").mock(
        return_value=httpx.Response(
            200,
            json={
                "nat_policies": [
                    {
                        "ipv4": {
                            "name": "sdk-nat",
                            "inbound": "any",
                            "outbound": "X1",
                            "source": {"any": True},
                            "translated_source": {"original": True},
                            "destination": {"any": True},
                            "translated_destination": {"original": True},
                            "service": {"any": True},
                            "translated_service": {"original": True},
                            "enable": True,
                        }
                    }
                ]
            },
        )
    )

    policy = NatPolicy(
        name="sdk-nat",
        inbound_interface="any",
        outbound_interface="X1",
        original_source="any",
        translated_source="original",
        original_destination="any",
        translated_destination="original",
        original_service="any",
        translated_service="original",
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        await client.nat_policies.create(policy)
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_access_rule_create_schema_fallback(mock_sonicwall) -> None:
    calls = {"count": 0}

    def create_handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(400, json=_schema_err("access_rules"))
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    mock_sonicwall.post("/access-rules/ipv4").mock(side_effect=create_handler)
    mock_sonicwall.get("/access-rules/ipv4/from/LAN/to/WAN/name/sdk-rule").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_rules": [
                    {"ipv4": {"name": "sdk-rule", "from": "LAN", "to": "WAN", "action": "deny"}}
                ]
            },
        )
    )

    rule = AccessRule(
        name="sdk-rule",
        **{"from": "LAN", "to": "WAN"},
        action=AccessRuleAction.DENY,
        source=RuleAddress(any=True),
        destination=RuleAddress(any=True),
        service=RuleService(any=True),
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        await client.access_rules.create(rule)
    assert calls["count"] == 2
