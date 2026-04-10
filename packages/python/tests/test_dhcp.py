"""Tests for DHCP lease resource fallback behavior."""

from __future__ import annotations

import httpx
import pytest
import respx

from sonicwall import SonicWallClient
from tests.conftest import AUTH_SUCCESS_RESPONSE, BASE_URL, HOST, PASSWORD, USERNAME


@pytest.mark.asyncio
async def test_dhcp_list_leases_fallback_endpoint_and_key() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        # Digest handshake then auth success
        auth_calls = {"count": 0}

        def auth_handler(_: httpx.Request) -> httpx.Response:
            auth_calls["count"] += 1
            if auth_calls["count"] % 2 == 1:
                return httpx.Response(
                    401,
                    json={
                        "status": {
                            "success": False,
                            "info": [{"code": 401, "message": "Unauthorized"}],
                        }
                    },
                    headers={
                        "WWW-Authenticate": (
                            'Digest realm="sonicwall", nonce="abc123", '
                            'algorithm=SHA-256, qop="auth-int"'
                        )
                    },
                )
            return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

        router.post("/auth").mock(side_effect=auth_handler)
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))

        # Primary endpoint missing; fallback endpoint works with alternative key.
        router.get("/dhcp/server/lease").mock(
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
        router.get("/dhcp/server/leases").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dhcp_server_leases": [
                        {"ip": "192.168.0.10", "mac": "aa:bb:cc:dd:ee:ff", "hostname": "client-1"}
                    ]
                },
            )
        )

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            leases = await client.dhcp.list_leases()

        assert len(leases) == 1
        assert str(leases[0].ip) == "192.168.0.10"
