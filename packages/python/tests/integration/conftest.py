"""Fixtures for live SonicWall integration tests."""

from __future__ import annotations

import pytest

from sonicwall._live_validation import (
    LiveCredentials,
    integration_write_enabled,
    live_device_configured,
    resolve_live_credentials,
)


@pytest.fixture(scope="session")
def live_credentials() -> LiveCredentials:
    if not live_device_configured():
        pytest.skip(
            "Live device not configured. Set SONICWALL_HOST and SONICWALL_PASS "
            "(or SW_HOST / SW_PASS)."
        )
    return resolve_live_credentials(require_password=True)


@pytest.fixture(scope="session")
def live_write_enabled() -> bool:
    return integration_write_enabled()
