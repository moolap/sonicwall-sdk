"""Tests for .env loading during live validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from sonicwall._live_validation import load_local_env, resolve_live_credentials


def test_load_local_env_reads_repo_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("dotenv")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SONICWALL_HOST=10.0.0.99\nSONICWALL_USER=labadmin\nSONICWALL_PASS=secret\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SONICWALL_HOST", raising=False)
    monkeypatch.delenv("SONICWALL_USER", raising=False)
    monkeypatch.delenv("SONICWALL_PASS", raising=False)

    load_local_env()
    creds = resolve_live_credentials(require_password=True)

    assert creds.host == "10.0.0.99"
    assert creds.username == "labadmin"
    assert creds.password == "secret"
