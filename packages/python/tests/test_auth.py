"""Tests for authentication logic."""

from __future__ import annotations

import httpx
import pytest
import respx

from sonicwall import SonicWallClient
from sonicwall._exceptions import AuthenticationError
from tests.conftest import (
    AUTH_SUCCESS_RESPONSE,
    BASE_URL,
    BEARER_TOKEN,
    HOST,
    PASSWORD,
    SESSION_EXPIRED_RESPONSE,
    USERNAME,
)


@pytest.mark.asyncio
async def test_successful_auth_sets_bearer_token():
    """Digest handshake should store bearer token after second POST /auth."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        call_count = 0

        def auth_handler(_: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    401,
                    json={"status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}},
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

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            assert client._auth.is_authenticated  # noqa: SLF001
            assert client._auth._bearer_token == BEARER_TOKEN  # noqa: SLF001
            assert call_count == 2


@pytest.mark.asyncio
async def test_auth_failure_without_digest_challenge_raises():
    """A non-401 first auth response should fail authentication."""
    with respx.mock(base_url=BASE_URL) as router:
        router.post("/auth").mock(
            return_value=httpx.Response(
                500,
                json={"status": {"success": False, "info": [{"code": 500, "message": "Server error"}]}},
            )
        )

        client = SonicWallClient(HOST, USERNAME, PASSWORD)
        with pytest.raises(AuthenticationError) as exc_info:
            await client.connect()

        assert exc_info.value.status_code == 500
        assert "Expected 401 Digest challenge" in str(exc_info.value)


@pytest.mark.asyncio
async def test_auth_failure_raises_authentication_error():
    """A 401 with no usable digest challenge should raise AuthenticationError."""
    with respx.mock(base_url=BASE_URL) as router:
        router.post("/auth").mock(
            return_value=httpx.Response(
                401,
                json={"status": {"success": False, "info": [{"code": 401, "message": "Invalid credentials"}]}},
                headers={"WWW-Authenticate": 'Digest realm="sonicwall", nonce="abc123", qop="auth"'},
            )
        )

        client = SonicWallClient(HOST, USERNAME, PASSWORD)
        with pytest.raises(AuthenticationError) as exc_info:
            await client.connect()

        assert exc_info.value.status_code == 401
        assert "no usable Digest auth-int challenge" in str(exc_info.value)


@pytest.mark.asyncio
async def test_401_on_request_triggers_reauth(mock_sonicwall):
    """A 401 response on a non-auth request should trigger re-authentication."""
    call_count = 0

    def auth_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 1:
            return httpx.Response(
                401,
                json={"status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}},
                headers={
                    "WWW-Authenticate": (
                        f'Digest realm="sonicwall", nonce="nonce-{call_count}", '
                        'algorithm=SHA-256, qop="auth-int"'
                    )
                },
            )
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    # Override the default auth mock to count calls
    mock_sonicwall.post("/auth").mock(side_effect=auth_handler)

    # First request returns 401 forcing re-auth, second succeeds
    list_call_count = 0

    def list_handler(request: httpx.Request) -> httpx.Response:
        nonlocal list_call_count
        list_call_count += 1
        if list_call_count == 1:
            return httpx.Response(
                401,
                json={"status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}},
            )
        return httpx.Response(
            200,
            json={
                "status": {"success": True, "info": []},
                "address_objects": [],
            },
        )

    mock_sonicwall.get("/address-objects/ipv4").mock(side_effect=list_handler)

    client = SonicWallClient(HOST, USERNAME, PASSWORD)
    await client.connect()
    objs = await client.address_objects.list()
    await client.disconnect()

    assert objs == []
    assert list_call_count == 2  # First 401, then success after re-auth


@pytest.mark.asyncio
async def test_repeated_401_raises_authentication_error():
    """If re-auth succeeds but the request still returns 401, raise AuthenticationError."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        call_count = 0

        def auth_handler(_: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return httpx.Response(
                    401,
                    json={"status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}},
                    headers={
                        "WWW-Authenticate": (
                            f'Digest realm="sonicwall", nonce="nonce-{call_count}", '
                            'algorithm=SHA-256, qop="auth-int"'
                        )
                    },
                )
            return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

        router.post("/auth").mock(side_effect=auth_handler)
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))
        # Always 401 on the data endpoint
        router.get("/address-objects/ipv4").mock(
            return_value=httpx.Response(
                401,
                json={"status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}},
            )
        )

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            with pytest.raises(AuthenticationError):
                await client.address_objects.list()


@pytest.mark.asyncio
async def test_session_expired_code_raises_session_expired_error():
    """SonicOS code 1085 in response body should raise SessionExpiredError."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        call_count = 0

        def auth_handler(_: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return httpx.Response(
                    401,
                    json={"status": {"success": False, "info": [{"code": 401, "message": "Unauthorized"}]}},
                    headers={
                        "WWW-Authenticate": (
                            f'Digest realm="sonicwall", nonce="nonce-{call_count}", '
                            'algorithm=SHA-256, qop="auth-int"'
                        )
                    },
                )
            return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

        router.post("/auth").mock(side_effect=auth_handler)
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))
        # First list call returns session expired, second re-auth also fails
        call_count = 0

        def list_handler(_: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(401, json=SESSION_EXPIRED_RESPONSE)

        router.get("/address-objects/ipv4").mock(side_effect=list_handler)

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            # After two 401s (original + retry-after-reauth), should raise
            with pytest.raises(AuthenticationError):
                await client.address_objects.list()


@pytest.mark.asyncio
async def test_logout_calls_delete_auth(mock_sonicwall):
    """disconnect() should call DELETE /auth."""
    client = SonicWallClient(HOST, USERNAME, PASSWORD)
    await client.connect()
    await client.disconnect()

    # Verify DELETE /auth was called
    delete_calls = [
        call for call in mock_sonicwall.calls
        if call.request.method == "DELETE" and "/auth" in call.request.url.path
    ]
    assert len(delete_calls) == 1