"""Firmware capability detection helpers."""

from __future__ import annotations

from ._exceptions import SonicWallError, SonicWallHTTPError


def firmware_limitation_message(status_code: int, message: str) -> str | None:
    """Return a short reason when SonicOS indicates a firmware/API limitation.

    Returns ``None`` when the error does not match known limitation patterns.
    """
    msg = message.lower()
    if "api not found" in msg:
        return "api_not_found"
    if "endpoint is incomplete" in msg or (
        status_code == 400 and "incomplete" in msg
    ):
        return "endpoint_incomplete"
    if "command" in msg and "not found" in msg:
        return "command_not_found"
    if status_code == 405 and "non config mode" in msg:
        return "non_config_mode"
    return None


def is_firmware_unsupported_error(exc: BaseException) -> bool:
    """True when *exc* reflects a known firmware/API limitation (not an SDK bug)."""
    if isinstance(exc, SonicWallHTTPError):
        reason = firmware_limitation_message(exc.status_code, exc.message)
        if reason is not None:
            return True
        sonicos_msg = exc.sonicos_message or ""
        return firmware_limitation_message(exc.status_code, sonicos_msg) is not None
    if isinstance(exc, SonicWallError):
        return firmware_limitation_message(0, str(exc)) is not None
    return False
