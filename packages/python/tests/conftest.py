"""Test fixtures for the SonicWall SDK."""

from __future__ import annotations

import httpx
import pytest
import respx

from sonicwall import SonicWallClient

# Shared test constants
HOST = "192.168.1.1"
BASE_URL = f"https://{HOST}/api/sonicos"
USERNAME = "admin"
PASSWORD = "password"
BEARER_TOKEN = "test-bearer-token"

# Sample address object response fixture data
ADDR_OBJ_HOST_RAW = {
    "address_object": {
        "ipv4": {
            "name": "my-server",
            "zone": "LAN",
            "host": {"ip": "10.0.0.100"},
        }
    }
}

ADDR_OBJ_NETWORK_RAW = {
    "address_object": {
        "ipv4": {
            "name": "internal-net",
            "zone": "LAN",
            "network": {"subnet": "10.0.0.0", "mask": "255.255.255.0"},
        }
    }
}

AUTH_SUCCESS_RESPONSE = {
    "status": {
        "success": True,
        "info": [
            {
                "level": "info",
                "code": 200,
                "message": "Success",
                "bearer_token": BEARER_TOKEN,
            }
        ],
    }
}

COMMIT_SUCCESS_RESPONSE = {
    "status": {
        "success": True,
        "info": [{"level": "info", "code": 200, "message": "Changes committed."}],
    }
}

NOT_FOUND_RESPONSE = {
    "status": {
        "success": False,
        "info": [{"level": "error", "code": 1030, "message": "Object not found"}],
    }
}

CONFLICT_RESPONSE = {
    "status": {
        "success": False,
        "info": [{"level": "error", "code": 1055, "message": "Object already exists"}],
    }
}

SESSION_EXPIRED_RESPONSE = {
    "status": {
        "success": False,
        "info": [{"level": "error", "code": 1085, "message": "Session expired"}],
    }
}


def make_list_response(*objects: dict) -> dict:
    """Wrap address object dicts in a SonicOS list response."""
    return {
        "status": {"success": True, "info": []},
        "address_objects": list(objects),
    }


def make_single_response(obj: dict) -> dict:
    """Wrap a single address object in a SonicOS get response."""
    return {
        "status": {"success": True, "info": []},
        **obj,
    }


@pytest.fixture
def mock_sonicwall():
    """respx router pre-wired with auth and basic CRUD endpoints."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        # Auth endpoint — Digest handshake:
        # first POST /auth returns 401 challenge, second returns token.
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

        # Auth logout — DELETE /auth
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))

        # Commit — POST /config/pending
        router.post("/config/pending").mock(
            return_value=httpx.Response(200, json=COMMIT_SUCCESS_RESPONSE)
        )

        # Rollback — DELETE /config/pending
        router.delete("/config/pending").mock(
            return_value=httpx.Response(200, json=COMMIT_SUCCESS_RESPONSE)
        )

        # Address objects list
        router.get("/address-objects/ipv4").mock(
            return_value=httpx.Response(
                200,
                json=make_list_response(ADDR_OBJ_HOST_RAW, ADDR_OBJ_NETWORK_RAW),
            )
        )

        # Address object get by name — my-server
        router.get("/address-objects/ipv4/name/my-server").mock(
            return_value=httpx.Response(
                200,
                json=make_single_response(ADDR_OBJ_HOST_RAW),
            )
        )

        # Address object create
        router.post("/address-objects/ipv4").mock(
            return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
        )

        # Address object update
        router.put("/address-objects/ipv4/name/my-server").mock(
            return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
        )

        # Address object delete
        router.delete("/address-objects/ipv4/name/my-server").mock(
            return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
        )

        yield router


@pytest.fixture
async def sonicwall_client(mock_sonicwall):
    """An authenticated SonicWallClient using the mock server."""
    client = SonicWallClient(HOST, USERNAME, PASSWORD, verify_ssl=False)
    await client.connect()
    yield client
    await client.disconnect()
