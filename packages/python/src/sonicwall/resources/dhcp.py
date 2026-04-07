"""DHCP resource — read access to SonicOS DHCP server leases."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.dhcp import DhcpLease
from ._base import BaseResource

if TYPE_CHECKING:
    from .._client import SonicWallClient


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
        return await self._list(
            self._BASE,
            list_key="dhcp_leases",
            item_key=None,
            model_class=DhcpLease,
        )