"""Integration tests against a real SonicWall (optional, env-gated)."""

from __future__ import annotations

import pytest

from sonicwall._live_validation import run_smoke, run_write_crud

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_live_smoke(live_credentials) -> None:
    errors = await run_smoke(
        live_credentials.host,
        live_credentials.username,
        live_credentials.password,
    )
    assert errors == 0, f"smoke validation reported {errors} failure(s)"


@pytest.mark.integration_write
@pytest.mark.asyncio
async def test_live_write_crud(live_credentials, live_write_enabled: bool) -> None:
    if not live_write_enabled:
        pytest.skip("Destructive write CRUD skipped. Set SONICWALL_INTEGRATION_WRITE=1 to enable.")
    exit_code = await run_write_crud(
        live_credentials.host,
        live_credentials.username,
        live_credentials.password,
    )
    assert exit_code == 0, "write CRUD validation reported hard failure(s)"
