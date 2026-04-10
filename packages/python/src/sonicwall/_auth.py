"""Session authentication manager for the SonicOS REST API."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
from urllib.parse import urlparse

import httpx

from ._exceptions import AuthenticationError, SessionExpiredError

logger = logging.getLogger(__name__)

# SonicOS status code indicating the session has expired
_SESSION_EXPIRED_CODE = 1085


# ---------------------------------------------------------------------------
# Digest auth-int implementation
# httpx supports qop=auth but NOT qop=auth-int (body-included integrity).
# SonicWall TZ270 (SonicOS 7.x) requires auth-int, so we implement it here.
# ---------------------------------------------------------------------------

def _parse_digest_challenge(www_auth: str) -> dict[str, str]:
    """Parse a single WWW-Authenticate: Digest ... header into a dict."""
    # Strip leading 'Digest ' token
    body = re.sub(r"^[Dd]igest\s+", "", www_auth.strip())
    params: dict[str, str] = {}
    for m in re.finditer(r'(\w+)=(?:"([^"]*?)"|([^,\s]+))', body):
        params[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return params


def _pick_challenge(response: httpx.Response) -> dict[str, str] | None:
    """Return the best Digest challenge from WWW-Authenticate headers.

    Prefers SHA-256 over SHA-256-sess over MD5. Requires qop to include
    auth-int (SonicOS requirement).
    """
    challenges: list[dict[str, str]] = []
    for value in response.headers.get_list("www-authenticate"):
        if value.lower().startswith("digest"):
            c = _parse_digest_challenge(value)
            if "auth-int" in c.get("qop", ""):
                challenges.append(c)

    if not challenges:
        return None

    def _priority(c: dict[str, str]) -> int:
        alg = c.get("algorithm", "MD5").upper()
        if alg == "SHA-256":
            return 0
        if alg == "SHA-256-SESS":
            return 1
        return 2

    return min(challenges, key=_priority)


def _build_digest_auth_header(
    method: str,
    url: str,
    body: bytes,
    username: str,
    password: str,
    challenge: dict[str, str],
) -> str:
    """Build an Authorization: Digest header for qop=auth-int."""
    algorithm = challenge.get("algorithm", "MD5").upper()
    realm = challenge["realm"]
    nonce = challenge["nonce"]
    opaque = challenge.get("opaque", "")

    # URI is path + query only
    parsed = urlparse(url)
    uri = parsed.path + (f"?{parsed.query}" if parsed.query else "")

    # Choose hash function
    if "SHA-256" in algorithm:
        def h(s: str) -> str:
            return hashlib.sha256(s.encode()).hexdigest()

        def hb(b: bytes) -> str:
            return hashlib.sha256(b).hexdigest()
    else:
        def h(s: str) -> str:
            return hashlib.md5(s.encode()).hexdigest()  # noqa: S324

        def hb(b: bytes) -> str:
            return hashlib.md5(b).hexdigest()  # noqa: S324

    cnonce = os.urandom(8).hex()
    nc = "00000001"

    # HA1
    ha1 = h(f"{username}:{realm}:{password}")
    if "SESS" in algorithm:
        ha1 = h(f"{ha1}:{nonce}:{cnonce}")

    # HA2 — auth-int includes hash of request body
    ha2 = h(f"{method}:{uri}:{hb(body)}")

    # Final response
    digest_response = h(f"{ha1}:{nonce}:{nc}:{cnonce}:auth-int:{ha2}")

    header = (
        f'Digest username="{username}", realm="{realm}", '
        f'nonce="{nonce}", uri="{uri}", '
        f'algorithm={algorithm}, '
        f'qop=auth-int, nc={nc}, cnonce="{cnonce}", '
        f'response="{digest_response}"'
    )
    if opaque:
        header += f', opaque="{opaque}"'
    return header


# ---------------------------------------------------------------------------
# Cookie / session helpers
# ---------------------------------------------------------------------------

def _extract_bearer_token(response: httpx.Response) -> str | None:
    """Extract the bearer_token from a successful SonicOS /auth response body."""
    try:
        body = response.json()
        info_list = body.get("status", {}).get("info", [])
        for item in info_list:
            token = item.get("bearer_token")
            if token:
                return str(token)
    except Exception:  # noqa: BLE001
        pass
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


# ---------------------------------------------------------------------------
# AuthManager
# ---------------------------------------------------------------------------

class AuthManager:
    """Manages SonicOS session authentication.

    SonicOS 7.x requires HTTP Digest auth with qop=auth-int (body integrity).
    httpx does not support auth-int, so we implement the handshake manually:
      1. POST /auth without credentials → 401 with Digest challenge
      2. Compute Authorization header with auth-int
      3. POST /auth again with the computed header → 200 + JWT bearer_token in body
    Subsequent requests use Authorization: Bearer <token>.
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._bearer_token: str | None = None
        self._lock = asyncio.Lock()
        self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated and self._bearer_token is not None

    async def authenticate(self, client: httpx.AsyncClient) -> None:
        """Perform Digest auth-int handshake against POST /auth."""
        auth_url = f"{self._base_url}/auth"
        body = b"{}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        logger.debug("Authenticating to %s (step 1 — get challenge)", auth_url)

        # Step 1: unauthenticated request to get the Digest challenge
        challenge_response = await client.post(auth_url, headers=headers, content=body)

        if challenge_response.status_code != 401:
            raise AuthenticationError(
                status_code=challenge_response.status_code,
                message=f"Expected 401 Digest challenge, got {challenge_response.status_code}",
                response_body=self._safe_json(challenge_response),
            )

        challenge = _pick_challenge(challenge_response)
        if not challenge:
            raise AuthenticationError(
                status_code=401,
                message="Server returned 401 but no usable Digest auth-int challenge",
                response_body=self._safe_json(challenge_response),
            )

        logger.debug(
            "Got Digest challenge: algorithm=%s realm=%s",
            challenge.get("algorithm"),
            challenge.get("realm"),
        )

        # Step 2: authenticated request with computed Digest header
        auth_header = _build_digest_auth_header(
            method="POST",
            url=auth_url,
            body=body,
            username=self._username,
            password=self._password,
            challenge=challenge,
        )
        authed_headers = {**headers, "Authorization": auth_header}

        logger.debug("Authenticating to %s (step 2 — send credentials)", auth_url)
        response = await client.post(auth_url, headers=authed_headers, content=body)

        if response.status_code == 401:
            raise AuthenticationError(
                status_code=401,
                message="Authentication failed: invalid username or password",
                response_body=self._safe_json(response),
            )

        if not response.is_success:
            raise AuthenticationError(
                status_code=response.status_code,
                message=f"Authentication failed with status {response.status_code}",
                response_body=self._safe_json(response),
            )

        # SonicOS 7.x returns a JWT bearer_token in the response body (not a cookie)
        token = _extract_bearer_token(response)
        if not token:
            raise AuthenticationError(
                status_code=response.status_code,
                message="Authentication succeeded but no bearer_token in response body",
                response_body=self._safe_json(response),
            )

        self._bearer_token = token
        self._authenticated = True
        logger.debug("Authenticated; bearer token acquired")

    async def ensure_authenticated(self, client: httpx.AsyncClient) -> None:
        """Ensure a valid session exists, re-authenticating if necessary."""
        if self.is_authenticated:
            return
        async with self._lock:
            if not self.is_authenticated:
                await self.authenticate(client)

    async def reauthenticate(self, client: httpx.AsyncClient) -> None:
        """Force re-authentication, discarding the existing token."""
        async with self._lock:
            self._authenticated = False
            self._bearer_token = None
            await self.authenticate(client)

    async def logout(self, client: httpx.AsyncClient) -> None:
        """Destroy the current session via DELETE /auth."""
        if not self.is_authenticated:
            return
        auth_url = f"{self._base_url}/auth"
        try:
            await client.delete(
                auth_url,
                headers={**self._auth_headers(), "Accept": "application/json"},
            )
            logger.debug("Logged out successfully")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Logout request failed (ignoring): %s", exc)
        finally:
            self._bearer_token = None
            self._authenticated = False

    def _auth_headers(self) -> dict[str, str]:
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    def check_response_for_session_expiry(self, response: httpx.Response) -> bool:
        if response.status_code == 401 and _is_session_expired(response):
            return True
        if response.is_success and _is_session_expired(response):
            return True
        return False

    def raise_if_session_expired(self, response: httpx.Response) -> None:
        if self.check_response_for_session_expiry(response):
            raise SessionExpiredError(
                status_code=response.status_code,
                message="SonicOS session expired; re-authentication required",
                response_body=self._safe_json(response),
            )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict:  # type: ignore[type-arg]
        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception:  # noqa: BLE001
            return {}