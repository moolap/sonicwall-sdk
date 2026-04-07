"""Tests for authentication logic."""

from __future__ import annotations

import pytest
import respx
import httpx

from sonicwall import SonicWallClient
from sonicwall._exceptions import AuthenticationError, SessionExpiredError
from tests.conftest import (
    HOST,
    USERNAME,
    PASSWORD,
    BASE_URL,
    SESSION_COOKIE,
    AUTH_SUCCESS_RESPONSE,
    SESSION_EXPIRED_RESPONSE,
)


@pytest.mark.asyncio
async def test_successful_auth_sets_cookie():
    """A successful POST /auth should store the smngsess cookie."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        router.post("/auth").mock(
            return_value=httpx.Response(
                200,
                json=AUTH_SUCCESS_RESPONSE,
                headers={"Set-Cookie": f"smngsess={SESSION_COOKIE}; Path=/; Secure"},
            )
        )
        router.delete("/auth").mock(return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE))

        async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
            assert client._auth.is_authenticated  # noqa: SLF001
            assert client._auth._session_cookie == SESSION_COOKIE  # noqa: SLF001


@pytest.mark.asyncio
async def test_auth_failure_raises_authentication_error():
    """A 401 from POST /auth should raise AuthenticationError."""
    with respx.mock(base_url=BASE_URL) as router:
        router.post("/auth").mock(
            return_value=httpx.Response(
                401,
                json={"status": {"success": False, "info": [{"code": 401, "message": "Invalid credentials"}]}},
            )
        )

        client = SonicWallClient(HOST, USERNAME, PASSWORD)
        with pytest.raises(AuthenticationError) as exc_info:
            await client.connect()

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_401_on_request_triggers_reauth(mock_sonicwall):
    """A 401 response on a non-auth request should trigger re-authentication."""
    call_count = 0

    def auth_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json=AUTH_SUCCESS_RESPONSE,
            headers={"Set-Cookie": f"smngsess=new_cookie_{call_count}; Path=/"},
        )

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
        router.post("/auth").mock(
            return_value=httpx.Response(
                200,
                json=AUTH_SUCCESS_RESPONSE,
                headers={"Set-Cookie": f"smngsess={SESSION_COOKIE}; Path=/"},
            )
        )
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
        router.post("/auth").mock(
            return_value=httpx.Response(
                200,
                json=AUTH_SUCCESS_RESPONSE,
                headers={"Set-Cookie": f"smngsess={SESSION_COOKIE}; Path=/"},
            )
        )
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