"""Fallback tests for get-by-name resource endpoints."""

from __future__ import annotations

import httpx
import pytest
import respx

from sonicwall import SonicWallClient
from tests.conftest import AUTH_SUCCESS_RESPONSE, BASE_URL, HOST, PASSWORD, USERNAME


def _auth_handler_factory() -> callable:
    calls = {"count": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] % 2 == 1:
            return httpx.Response(
                401,
                json={
                    "status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}
                },
                headers={
                    "WWW-Authenticate": (
                        'Digest realm="sonicwall", nonce="abc123", algorithm=SHA-256, qop="auth-int"'
                    )
                },
            )
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    return handler


@pytest.mark.asyncio
async def test_service_object_get_falls_back_to_list_on_404() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        router.post("/auth").mock(side_effect=_auth_handler_factory())
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))
        router.get("/service-objects/name/HTTP").mock(
            return_value=httpx.Response(
                404,
                json={
                    "status": {
                        "success": False,
                        "info": [{"code": "E_NOT_FOUND", "message": "API not found."}],
                    }
                },
            )
        )
        router.get("/service-objects").mock(
            return_value=httpx.Response(
                200,
                json={
                    "service_objects": [
                        {"name": "HTTP", "protocol": {"tcp": {"begin": 80, "end": 80}}}
                    ]
                },
            )
        )

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            obj = await client.service_objects.get("HTTP")
        assert obj.name == "HTTP"


@pytest.mark.asyncio
async def test_nat_policy_get_falls_back_to_list_on_404() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        router.post("/auth").mock(side_effect=_auth_handler_factory())
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))
        router.get("/nat-policies/ipv4/name/Default%20NAT%20Policy").mock(
            return_value=httpx.Response(
                404,
                json={
                    "status": {
                        "success": False,
                        "info": [{"code": "E_NOT_FOUND", "message": "API not found."}],
                    }
                },
            )
        )
        router.get("/nat-policies/ipv4").mock(
            return_value=httpx.Response(
                200,
                json={
                    "nat_policies": [
                        {
                            "ipv4": {
                                "name": "Default NAT Policy",
                                "inbound": "X0",
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

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            policy = await client.nat_policies.get("Default NAT Policy")
        assert policy.name == "Default NAT Policy"


@pytest.mark.asyncio
async def test_access_rule_get_handles_list_envelope() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        router.post("/auth").mock(side_effect=_auth_handler_factory())
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))
        router.get("/access-rules/ipv4/from/LAN/to/LAN/name/Rule1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_rules": [
                        {"ipv4": {"name": "Rule1", "from": "LAN", "to": "LAN", "action": "allow"}}
                    ]
                },
            )
        )
        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            rule = await client.access_rules.get("LAN", "LAN", "Rule1")
        assert rule.name == "Rule1"
