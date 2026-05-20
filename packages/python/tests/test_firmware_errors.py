"""Tests for firmware capability error classification."""

from __future__ import annotations

import pytest

from sonicwall._exceptions import SonicWallHTTPError, UnsupportedEndpointError
from sonicwall._firmware import firmware_limitation_message, is_firmware_unsupported_error
from sonicwall._http import HTTPClient


@pytest.mark.parametrize(
    ("status_code", "message", "expected"),
    [
        (404, "API not found", "api_not_found"),
        (400, "API endpoint is incomplete", "endpoint_incomplete"),
        (400, "incomplete", "endpoint_incomplete"),
        (404, "command xyz not found", "command_not_found"),
        (405, "Non config mode", "non_config_mode"),
        (500, "Internal server error", None),
    ],
)
def test_firmware_limitation_message(status_code: int, message: str, expected: str | None) -> None:
    assert firmware_limitation_message(status_code, message) == expected


def test_is_firmware_unsupported_error_from_unsupported_endpoint() -> None:
    exc = UnsupportedEndpointError(400, "API endpoint is incomplete", reason="endpoint_incomplete")
    assert is_firmware_unsupported_error(exc)


def test_http_client_raises_unsupported_endpoint_error() -> None:
    import httpx

    client = HTTPClient.__new__(HTTPClient)
    response = httpx.Response(
        400,
        json={
            "status": {
                "success": False,
                "info": [{"code": 400, "message": "API endpoint is incomplete"}],
            }
        },
    )
    with pytest.raises(UnsupportedEndpointError) as exc_info:
        client._raise_for_status(response)
    assert exc_info.value.reason == "endpoint_incomplete"
