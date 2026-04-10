"""Tests for the AddressObjects resource."""

from __future__ import annotations

import pytest
import respx
import httpx

from sonicwall import SonicWallClient
from sonicwall._exceptions import ConflictError, NotFoundError
from sonicwall.models import AddressObject, AddressObjectType
from tests.conftest import (
    HOST,
    USERNAME,
    PASSWORD,
    BASE_URL,
    AUTH_SUCCESS_RESPONSE,
    ADDR_OBJ_HOST_RAW,
    ADDR_OBJ_NETWORK_RAW,
    NOT_FOUND_RESPONSE,
    CONFLICT_RESPONSE,
    make_list_response,
    make_single_response,
)


@pytest.mark.asyncio
async def test_list_returns_all_objects(sonicwall_client):
    """list() should return all address objects."""
    objs = await sonicwall_client.address_objects.list()
    assert len(objs) == 2
    assert objs[0].name == "my-server"
    assert objs[0].type == AddressObjectType.HOST
    assert str(objs[0].host) == "10.0.0.100"
    assert objs[1].name == "internal-net"
    assert objs[1].type == AddressObjectType.NETWORK


@pytest.mark.asyncio
async def test_list_empty(mock_sonicwall):
    """list() should return an empty list when there are no objects."""
    mock_sonicwall.get("/address-objects/ipv4").mock(
        return_value=httpx.Response(
            200,
            json={"status": {"success": True, "info": []}, "address_objects": []},
        )
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        objs = await client.address_objects.list()
    assert objs == []


@pytest.mark.asyncio
async def test_list_handles_host_address_key_shape(mock_sonicwall):
    """list() should parse host objects that use host.address instead of host.ip."""
    mock_sonicwall.get("/address-objects/ipv4").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": {"success": True, "info": []},
                "address_objects": [
                    {
                        "address_object": {
                            "ipv4": {
                                "name": "my-server",
                                "zone": "LAN",
                                "host": {"address": "10.0.0.100"},
                            }
                        }
                    }
                ],
            },
        )
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        objs = await client.address_objects.list()
    assert len(objs) == 1
    assert str(objs[0].host) == "10.0.0.100"


@pytest.mark.asyncio
async def test_list_skips_unparsable_host_entry(mock_sonicwall):
    """list() should skip malformed entries instead of failing entire list."""
    mock_sonicwall.get("/address-objects/ipv4").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": {"success": True, "info": []},
                "address_objects": [
                    {"address_object": {"ipv4": {"name": "broken", "zone": "LAN", "host": {}}}},
                    {"address_object": {"ipv4": {"name": "good", "zone": "LAN", "host": {"ip": "10.0.0.2"}}}},
                ],
            },
        )
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        objs = await client.address_objects.list()
    assert len(objs) == 1
    assert objs[0].name == "good"


@pytest.mark.asyncio
async def test_get_existing_object(sonicwall_client):
    """get() should return the address object for a known name."""
    obj = await sonicwall_client.address_objects.get("my-server")
    assert obj.name == "my-server"
    assert obj.type == AddressObjectType.HOST
    assert str(obj.host) == "10.0.0.100"
    assert obj.zone == "LAN"


@pytest.mark.asyncio
async def test_get_handles_list_envelope_shape(mock_sonicwall):
    """get() should parse firmware shape that returns address_objects list."""
    mock_sonicwall.get("/address-objects/ipv4/name/my-server").mock(
        return_value=httpx.Response(
            200,
            json={
                "address_objects": [
                    {"ipv4": {"name": "my-server", "zone": "LAN", "host": {"ip": "10.0.0.100"}}}
                ]
            },
        )
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        obj = await client.address_objects.get("my-server")
    assert obj.name == "my-server"
    assert str(obj.host) == "10.0.0.100"


@pytest.mark.asyncio
async def test_get_not_found_raises_error(mock_sonicwall):
    """get() should raise NotFoundError when the object doesn't exist."""
    mock_sonicwall.get("/address-objects/ipv4/name/ghost").mock(
        return_value=httpx.Response(200, json=NOT_FOUND_RESPONSE)
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        with pytest.raises(NotFoundError) as exc_info:
            await client.address_objects.get("ghost")
    assert exc_info.value.status_code == 200  # SonicOS returns 200 with success=false
    assert exc_info.value.sonicos_code == 1030


@pytest.mark.asyncio
async def test_create_new_object(mock_sonicwall):
    """create() should POST the object and return it."""
    new_obj = AddressObject(
        name="new-host",
        type=AddressObjectType.HOST,
        host="192.168.1.50",
        zone="LAN",
    )
    mock_sonicwall.post("/address-objects/ipv4").mock(
        return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
    )
    mock_sonicwall.get("/address-objects/ipv4/name/new-host").mock(
        return_value=httpx.Response(
            200,
            json=make_single_response(
                {"address_object": {"ipv4": {"name": "new-host", "zone": "LAN", "host": {"ip": "192.168.1.50"}}}}
            ),
        )
    )

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        created = await client.address_objects.create(new_obj)

    assert created.name == "new-host"
    assert str(created.host) == "192.168.1.50"


@pytest.mark.asyncio
async def test_create_retries_with_array_payload_on_schema_error(mock_sonicwall):
    """create() should retry with address_objects[] payload on firmware schema error."""
    calls = {"count": 0}

    def create_handler(_: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(
                400,
                json={
                    "status": {
                        "success": False,
                        "info": [
                            {
                                "level": "error",
                                "code": 400,
                                "message": "Schema validation error: property 'address_objects' expected '['",
                            }
                        ],
                    }
                },
            )
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    mock_sonicwall.post("/address-objects/ipv4").mock(side_effect=create_handler)
    mock_sonicwall.get("/address-objects/ipv4/name/new-host").mock(
        return_value=httpx.Response(
            200,
            json=make_single_response(
                {"address_object": {"ipv4": {"name": "new-host", "zone": "LAN", "host": {"ip": "192.168.1.50"}}}}
            ),
        )
    )

    new_obj = AddressObject(
        name="new-host",
        type=AddressObjectType.HOST,
        host="192.168.1.50",
        zone="LAN",
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        created = await client.address_objects.create(new_obj)

    assert created.name == "new-host"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_create_conflict_raises_error(mock_sonicwall):
    """create() should raise ConflictError when the object already exists."""
    mock_sonicwall.post("/address-objects/ipv4").mock(
        return_value=httpx.Response(200, json=CONFLICT_RESPONSE)
    )

    obj = AddressObject(
        name="my-server",
        type=AddressObjectType.HOST,
        host="10.0.0.1",
        zone="LAN",
    )
    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        with pytest.raises(ConflictError):
            await client.address_objects.create(obj)


@pytest.mark.asyncio
async def test_update_existing_object(mock_sonicwall):
    """update() should PUT the updated object and return it."""
    updated_obj = AddressObject(
        name="my-server",
        type=AddressObjectType.HOST,
        host="10.0.0.200",
        zone="LAN",
    )
    mock_sonicwall.put("/address-objects/ipv4/name/my-server").mock(
        return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
    )
    mock_sonicwall.get("/address-objects/ipv4/name/my-server").mock(
        return_value=httpx.Response(
            200,
            json=make_single_response(
                {"address_object": {"ipv4": {"name": "my-server", "zone": "LAN", "host": {"ip": "10.0.0.200"}}}}
            ),
        )
    )

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        result = await client.address_objects.update("my-server", updated_obj)

    assert str(result.host) == "10.0.0.200"


@pytest.mark.asyncio
async def test_delete_existing_object(sonicwall_client):
    """delete() should call DELETE on the correct endpoint."""
    # Should not raise
    await sonicwall_client.address_objects.delete("my-server")


@pytest.mark.asyncio
async def test_delete_not_found_raises_error(mock_sonicwall):
    """delete() should raise NotFoundError when the object doesn't exist."""
    mock_sonicwall.delete("/address-objects/ipv4/name/ghost").mock(
        return_value=httpx.Response(200, json=NOT_FOUND_RESPONSE)
    )

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        with pytest.raises(NotFoundError):
            await client.address_objects.delete("ghost")


@pytest.mark.asyncio
async def test_ensure_creates_new_object(mock_sonicwall):
    """ensure() should create the object and return (obj, True) when it doesn't exist."""
    new_obj = AddressObject(
        name="brand-new",
        type=AddressObjectType.HOST,
        host="172.16.0.1",
        zone="DMZ",
    )

    # First get returns not found (object doesn't exist)
    mock_sonicwall.get("/address-objects/ipv4/name/brand-new").mock(
        side_effect=[
            httpx.Response(200, json=NOT_FOUND_RESPONSE),
            # Second get (after create) returns the object
            httpx.Response(
                200,
                json=make_single_response(
                    {"address_object": {"ipv4": {"name": "brand-new", "zone": "DMZ", "host": {"ip": "172.16.0.1"}}}}
                ),
            ),
        ]
    )
    mock_sonicwall.post("/address-objects/ipv4").mock(
        return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
    )

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        result, was_created = await client.address_objects.ensure(new_obj)

    assert was_created is True
    assert result.name == "brand-new"
    assert str(result.host) == "172.16.0.1"


@pytest.mark.asyncio
async def test_ensure_updates_existing_object(mock_sonicwall):
    """ensure() should update the object and return (obj, False) when it exists."""
    existing_obj = AddressObject(
        name="my-server",
        type=AddressObjectType.HOST,
        host="10.0.0.200",
        zone="LAN",
    )

    mock_sonicwall.get("/address-objects/ipv4/name/my-server").mock(
        side_effect=[
            # First call: object exists
            httpx.Response(200, json=make_single_response(ADDR_OBJ_HOST_RAW)),
            # Second call: after update
            httpx.Response(
                200,
                json=make_single_response(
                    {"address_object": {"ipv4": {"name": "my-server", "zone": "LAN", "host": {"ip": "10.0.0.200"}}}}
                ),
            ),
        ]
    )
    mock_sonicwall.put("/address-objects/ipv4/name/my-server").mock(
        return_value=httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)
    )

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        result, was_created = await client.address_objects.ensure(existing_obj)

    assert was_created is False
    assert str(result.host) == "10.0.0.200"


@pytest.mark.asyncio
async def test_pending_context_commits_on_success(mock_sonicwall):
    """pending() context manager should commit on clean exit."""
    commit_called = False

    def commit_handler(_: httpx.Request) -> httpx.Response:
        nonlocal commit_called
        commit_called = True
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    mock_sonicwall.post("/config/pending").mock(side_effect=commit_handler)

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        async with client.pending():
            pass  # No-op body

    assert commit_called


@pytest.mark.asyncio
async def test_pending_context_rolls_back_on_exception(mock_sonicwall):
    """pending() context manager should rollback on exception."""
    rollback_called = False

    def rollback_handler(_: httpx.Request) -> httpx.Response:
        nonlocal rollback_called
        rollback_called = True
        return httpx.Response(200, json=AUTH_SUCCESS_RESPONSE)

    mock_sonicwall.delete("/config/pending").mock(side_effect=rollback_handler)

    async with SonicWallClient(HOST, USERNAME, PASSWORD) as client:
        with pytest.raises(ValueError):
            async with client.pending():
                raise ValueError("Simulated error")

    assert rollback_called