"""Interfaces resource — read-only access to SonicOS network interfaces."""

from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING

from ..models.interface import Interface
from ._base import BaseResource

if TYPE_CHECKING:
    from .._client import SonicWallClient


class InterfacesResource(BaseResource):
    """Read-only access to SonicOS network interfaces.

    Endpoint base: ``/interfaces``

    SonicOS does support interface modification via PUT, but the interface
    configuration is sensitive (IP changes can sever the management connection)
    and varies widely by firmware version. This SDK exposes interfaces as
    read-only. Use direct API calls via the http client for advanced use cases.
    """

    _BASE = "/interfaces"

    def __init__(self, client: SonicWallClient) -> None:
        super().__init__(client)

    async def list(self) -> list[Interface]:
        """Return all network interfaces."""
        return await self._list(
            self._BASE,
            list_key="interfaces",
            item_key="interface",
            model_class=Interface,
        )

    async def get(self, name: str) -> Interface:
        """Fetch a specific interface by name (e.g. "X0", "X1").

        Raises:
            NotFoundError: if the interface does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        response = await self._get(f"{self._BASE}/name/{encoded_name}")
        return Interface.from_api_response(response)
