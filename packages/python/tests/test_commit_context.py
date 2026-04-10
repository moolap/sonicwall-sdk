"""Tests for pending transaction config-mode behavior."""

from __future__ import annotations

from typing import Any

import pytest

from sonicwall._commit import CommitContext
from sonicwall._exceptions import SonicWallHTTPError


class _FakeHTTPClient:
    def __init__(self, failures: dict[tuple[str, str], int] | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self.failures = failures or {}

    async def request(self, method: str, path: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, path))
        status = self.failures.get((method, path))
        if status is not None:
            raise SonicWallHTTPError(status, "failed")
        return {"status": {"success": True, "info": []}}


@pytest.mark.asyncio
async def test_pending_enters_and_exits_config_mode_when_supported() -> None:
    http = _FakeHTTPClient(
        failures={
            ("POST", "/config/mode"): 404,  # first candidate fails
            ("DELETE", "/config/mode"): 404,
        }
    )
    ctx = CommitContext(http, depth_tracker=[0])

    async with ctx:
        pass

    assert ("POST", "/config-mode") in http.calls
    assert ("POST", "/config/pending") in http.calls
    assert ("DELETE", "/config-mode") in http.calls


@pytest.mark.asyncio
async def test_nested_pending_only_outer_handles_transaction() -> None:
    http = _FakeHTTPClient()
    depth = [0]
    outer = CommitContext(http, depth_tracker=depth)
    inner = CommitContext(http, depth_tracker=depth)

    async with outer:
        async with inner:
            pass

    # only one commit call for outermost context
    assert http.calls.count(("POST", "/config/pending")) == 1
