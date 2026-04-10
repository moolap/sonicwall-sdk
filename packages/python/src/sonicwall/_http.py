"""HTTP client wrapper for the SonicOS REST API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ._auth import AuthManager
from ._exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    SessionExpiredError,
    SonicWallHTTPError,
)

logger = logging.getLogger(__name__)

# SonicOS internal status codes
_SONICOS_CODE_NOT_FOUND = 1030
_SONICOS_CODE_ALREADY_EXISTS = 1055


def _extract_sonicos_code(body: dict[str, Any]) -> int | None:
    try:
        info_list = body["status"]["info"]
        if info_list:
            code = info_list[0].get("code")
            return int(code) if code is not None else None
    except (KeyError, TypeError, IndexError):
        pass
    return None


def _extract_sonicos_message(body: dict[str, Any]) -> str:
    try:
        info_list = body["status"]["info"]
        if info_list:
            msg = info_list[0].get("message", "")
            return str(msg)
    except (KeyError, TypeError, IndexError):
        pass
    return ""


class HTTPClient:
    """Thin async HTTP wrapper around httpx.AsyncClient.

    Handles:
    - Injecting auth cookies on every request
    - Automatic single-retry on 401 (re-authenticates then retries once)
    - Mapping HTTP status codes and SonicOS error codes to typed exceptions
    """

    def __init__(
        self,
        base_url: str,
        auth_manager: AuthManager,
        *,
        verify_ssl: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = auth_manager
        self._client = httpx.AsyncClient(
            verify=verify_ssl,
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the SonicOS API.

        Automatically injects the session cookie, retries once on 401.
        Returns the parsed JSON body on success.
        """
        url = f"{self._base_url}/{path.lstrip('/')}"

        try:
            await self._auth.ensure_authenticated(self._client)
        except Exception:
            raise

        response = await self._do_request(method, url, json=json, params=params)

        # Handle session expiry — re-auth once then retry
        if response.status_code == 401 or self._auth.check_response_for_session_expiry(response):
            logger.debug("Session appears expired; re-authenticating")
            await self._auth.reauthenticate(self._client)
            response = await self._do_request(method, url, json=json, params=params)
            # If still 401 after re-auth, raise AuthenticationError
            if response.status_code == 401:
                self._raise_for_status(response)

        self._raise_for_status(response)
        body: dict[str, Any] = self._safe_json(response)
        return body

    async def _do_request(
        self,
        method: str,
        url: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers: dict[str, str] = {"Accept": "application/json"}
        if json is not None:
            headers["Content-Type"] = "application/json"

        # Inject bearer token
        if self._auth._bearer_token:
            headers["Authorization"] = f"Bearer {self._auth._bearer_token}"

        try:
            return await self._client.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
            )
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Cannot connect to SonicWall at {url}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ConnectionError(f"Request to {url} timed out: {exc}") from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Map HTTP status codes and SonicOS body codes to typed exceptions."""
        if response.is_success:
            # Even on 200, SonicOS may indicate failure in the body
            body = self._safe_json(response)
            success = body.get("status", {}).get("success", True)
            if not success:
                code = _extract_sonicos_code(body)
                msg = _extract_sonicos_message(body) or "API returned success=false"
                if code == _SONICOS_CODE_NOT_FOUND:
                    raise NotFoundError(
                        status_code=response.status_code,
                        message=msg,
                        response_body=body,
                    )
                if code == _SONICOS_CODE_ALREADY_EXISTS:
                    raise ConflictError(
                        status_code=response.status_code,
                        message=msg,
                        response_body=body,
                    )
                if code == SessionExpiredError.SESSION_EXPIRED_CODE:
                    raise SessionExpiredError(
                        status_code=response.status_code,
                        message="Session expired",
                        response_body=body,
                    )
                raise SonicWallHTTPError(
                    status_code=response.status_code,
                    message=msg,
                    response_body=body,
                )
            return

        body = self._safe_json(response)
        msg = _extract_sonicos_message(body) or response.reason_phrase or "Unknown error"

        if response.status_code == 401:
            code = _extract_sonicos_code(body)
            if code == SessionExpiredError.SESSION_EXPIRED_CODE:
                raise SessionExpiredError(
                    status_code=401,
                    message="Session expired",
                    response_body=body,
                )
            raise AuthenticationError(
                status_code=401,
                message=msg,
                response_body=body,
            )
        if response.status_code == 403:
            raise AuthorizationError(
                status_code=403,
                message=msg,
                response_body=body,
            )
        if response.status_code == 404:
            raise NotFoundError(
                status_code=404,
                message=msg,
                response_body=body,
            )
        if response.status_code == 409:
            raise ConflictError(
                status_code=409,
                message=msg,
                response_body=body,
            )
        if response.status_code == 429:
            raise RateLimitError(
                status_code=429,
                message=msg,
                response_body=body,
            )
        raise SonicWallHTTPError(
            status_code=response.status_code,
            message=msg,
            response_body=body,
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception:
            return {}

    async def aclose(self) -> None:
        await self._client.aclose()
