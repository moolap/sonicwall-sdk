"""Exception hierarchy for the SonicWall SDK."""

from __future__ import annotations

from typing import Any


class SonicWallError(Exception):
    """Base class for all SonicWall SDK exceptions."""


class SonicWallHTTPError(SonicWallError):
    """Raised when the SonicOS API returns a non-successful HTTP status code."""

    def __init__(
        self,
        status_code: int,
        message: str,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response_body = response_body or {}
        super().__init__(f"HTTP {status_code}: {message}")

    @property
    def sonicos_code(self) -> int | None:
        """Return the SonicOS internal status code if present in the response body."""
        try:
            info_list = self.response_body["status"]["info"]
            if info_list:
                return int(info_list[0].get("code", 0)) or None
        except (KeyError, TypeError, IndexError):
            pass
        return None

    @property
    def sonicos_message(self) -> str | None:
        """Return the SonicOS error message from the response body if present."""
        try:
            info_list = self.response_body["status"]["info"]
            if info_list:
                return str(info_list[0].get("message", ""))
        except (KeyError, TypeError, IndexError):
            pass
        return None


class AuthenticationError(SonicWallHTTPError):
    """Raised when authentication fails (wrong credentials or session invalid)."""


class AuthorizationError(SonicWallHTTPError):
    """Raised when the authenticated user lacks permission for the operation."""


class NotFoundError(SonicWallHTTPError):
    """Raised when the requested resource does not exist."""


class ConflictError(SonicWallHTTPError):
    """Raised when creating a resource that already exists."""


class RateLimitError(SonicWallHTTPError):
    """Raised when the API rate limit is exceeded."""


class CommitError(SonicWallError):
    """Raised when committing pending configuration changes fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)


class RollbackError(SonicWallError):
    """Raised when rolling back pending configuration changes fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)


class ConnectionError(SonicWallError):
    """Raised when a network connection to the SonicWall cannot be established."""


class SessionExpiredError(AuthenticationError):
    """Raised when the SonicOS session has expired and re-authentication is needed.

    SonicOS returns status code 1085 in the response body when the session is
    no longer valid. This is a subclass of AuthenticationError.
    """

    # SonicOS internal code for session expiry
    SESSION_EXPIRED_CODE = 1085


class UnsupportedEndpointError(SonicWallHTTPError):
    """Raised when SonicOS reports an endpoint is missing or not usable on this firmware.

    Examples: ``API not found``, ``endpoint is incomplete``, ``Non config mode``.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        reason: str,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        self.reason = reason
        super().__init__(status_code, message, response_body)
