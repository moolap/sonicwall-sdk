"""DHCP resource — read access to SonicOS DHCP server leases."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .._exceptions import NotFoundError
from ..models.dhcp import DhcpLease
from ._base import BaseResource

if TYPE_CHECKING:
    from .._client import SonicWallClient

logger = logging.getLogger(__name__)


class DhcpResource(BaseResource):
    """Read access to SonicOS DHCP server leases.

    Endpoint: ``/dhcp/server/lease``

    SonicOS allows listing active leases. Creating and deleting static
    reservations is supported via separate endpoints; those are available
    via direct HTTP client calls for now.
    """

    _BASE = "/dhcp/server/lease"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

    async def list_leases(self) -> list[DhcpLease]:
        """Return all active DHCP server leases."""
        candidate_paths = [
            self._BASE,
            "/dhcp/server/leases",
            "/dhcp/leases",
            "/dhcp-server/lease",
        ]
        candidate_keys = ["dhcp_leases", "dhcp_server_leases", "leases"]

        last_not_found: Exception | None = None
        for path in candidate_paths:
            try:
                body = await self._get(path)
            except NotFoundError as exc:
                last_not_found = exc
                continue

            items = None
            for key in candidate_keys:
                raw = body.get(key)
                if isinstance(raw, list):
                    items = raw
                    break
            if items is None:
                # Some firmware may return successful status with empty payload.
                if body.get("status", {}).get("success") is True:
                    return []
                logger.warning("Unexpected DHCP lease response shape on %s: %r", path, body)
                return []

            result: list[DhcpLease] = []
            for item in items:
                try:
                    result.append(DhcpLease.from_api_response(item))
                except Exception:  # noqa: BLE001
                    logger.warning("Skipping unparsable DHCP lease item from %s: %r", path, item)
            return result

        if last_not_found:
            raise last_not_found
        return []