"""Session authentication manager for the SonicOS REST API."""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import TYPE_CHECKING

import httpx

from ._exceptions import AuthenticationError, SessionExpiredError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# SonicOS status code indicating the session has expired
_SESSION_EXPIRED_CODE = 1085


def _build_basic_auth_header(username: str, password: str) -> str:
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _extract_session_cookie(response: httpx.Response) -> str | None:
    """Extract the smngsess cookie value from a Set-Cookie header."""
    cookie = response.cookies.get("smngsess")
    if cookie:
        return cookie
    # Fallback: parse Set-Cookie header directly
    for header_value in response.headers.get_list("set-cookie"):
        if "smngsess=" in header_value:
            for part in header_value.split(";"):
                part = part.strip()
                if part.startswith("smngsess="):
                    return part[len("smngsess="):]
    return None


def _is_session_expired(response: httpx.Response) -> bool:
    """Return True if the response body indicates SonicOS session expiry."""
    try:
        body = response.json()
        info_list = body.get("status", {}).get("info", [])
        for item in info_list:
            if item.get("code") == _SESSION_EXPIRED_CODE:
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


class AuthManager:
    """Manages SonicOS session authentication.

    Handles login, logout, session cookie injection, automatic re-authentication
    on session expiry, and concurrent-safe re-auth using an asyncio.Lock.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._session_cookie: str | None = None
        self._lock = asyncio.Lock()
        self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated and self._session_cookie is not None

    async def authenticate(self, client: httpx.AsyncClient) -> None:
        """Perform initial authentication against POST /auth."""
        auth_url = f"{self._base_url}/auth"
        headers = {
            "Authorization": _build_basic_auth_header(self._username, self._password),
            "Content-Type": "application/json",
        }
        logger.debug("Authenticating to %s", auth_url)

        response = await client.post(auth_url, headers=headers, content=b"{}")

        if response.status_code == 401:
            raise AuthenticationError(
                status_code=401,
                message="Authentication failed: invalid username or password",
                response_body=self._safe_json(response),
            )

        if not response.is_success:
            raise AuthenticationError(
                status_code=response.status_code,
                message=f"Authentication request failed with status {response.status_code}",
                response_body=self._safe_json(response),
            )

        cookie = _extract_session_cookie(response)
        if not cookie:
            raise AuthenticationError(
                status_code=response.status_code,
                message="Authentication succeeded but no smngsess cookie was returned",
                response_body=self._safe_json(response),
            )

        self._session_cookie = cookie
        self._authenticated = True
        logger.debug("Authenticated successfully; session cookie acquired")

    async def ensure_authenticated(self, client: httpx.AsyncClient) -> None:
        """Ensure a valid session exists, re-authenticating if necessary.

        Uses an asyncio.Lock to prevent concurrent callers from triggering
        multiple simultaneous re-authentication requests.
        """
        if self.is_authenticated:
            return
        async with self._lock:
            # Double-check after acquiring the lock — another coroutine may
            # have already re-authenticated while we were waiting.
            if not self.is_authenticated:
                await self.authenticate(client)

    async def reauthenticate(self, client: httpx.AsyncClient) -> None:
        """Force re-authentication, discarding the existing session.

        Called after receiving a 401 or session-expired response.
        """
        async with self._lock:
            # Reset auth state so ensure_authenticated will re-auth
            self._authenticated = False
            self._session_cookie = None
            await self.authenticate(client)

    async def logout(self, client: httpx.AsyncClient) -> None:
        """Destroy the current session via DELETE /auth."""
        if not self.is_authenticated:
            return

        auth_url = f"{self._base_url}/auth"
        try:
            await client.delete(
                auth_url,
                headers=self._auth_headers(),
            )
            logger.debug("Logged out successfully")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Logout request failed (ignoring): %s", exc)
        finally:
            self._session_cookie = None
            self._authenticated = False

    def inject_auth(self, request: httpx.Request) -> httpx.Request:
        """Add the session cookie to an outgoing request."""
        if self._session_cookie:
            request.headers["Cookie"] = f"smngsess={self._session_cookie}"
        return request

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._session_cookie:
            headers["Cookie"] = f"smngsess={self._session_cookie}"
        return headers

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict:  # type: ignore[type-arg]
        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception:  # noqa: BLE001
            return {}

    def check_response_for_session_expiry(self, response: httpx.Response) -> bool:
        """Return True if the response indicates the session has expired."""
        if response.status_code == 401 and _is_session_expired(response):
            return True
        # SonicOS sometimes returns 200 with success=false and code 1085
        if response.is_success and _is_session_expired(response):
            return True
        return False

    def raise_if_session_expired(self, response: httpx.Response) -> None:
        """Raise SessionExpiredError if the response indicates session expiry."""
        if self.check_response_for_session_expiry(response):
            raise SessionExpiredError(
                status_code=response.status_code,
                message="SonicOS session has expired; re-authentication required",
                response_body=self._safe_json(response),
            )