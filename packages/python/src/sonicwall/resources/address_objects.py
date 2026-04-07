"""AddressObjects resource — full CRUD for IPv4 address objects."""

from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING

from ..models.address_object import AddressObject
from ._base import BaseResource
from .._exceptions import ConflictError, NotFoundError

if TYPE_CHECKING:
    from .._client import SonicWallClient


class AddressObjectsResource(BaseResource):
    """CRUD operations for SonicOS IPv4 address objects.

    Endpoint base: ``/address-objects/ipv4``
    """

    _BASE = "/address-objects/ipv4"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

    async def list(self) -> list[AddressObject]:
        """Return all IPv4 address objects."""
        return await self._list(
            self._BASE,
            list_key="address_objects",
            item_key="address_object",
            model_class=AddressObject,
        )

    async def get(self, name: str) -> AddressObject:
        """Fetch a single address object by name.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        response = await self._get(f"{self._BASE}/name/{encoded_name}")
        return AddressObject.from_api_response(response)

    async def create(self, obj: AddressObject) -> AddressObject:
        """Create a new IPv4 address object.

        Raises:
            ConflictError: if an object with the same name already exists.
        """
        await self._post(self._BASE, obj.to_api_dict())
        # SonicOS does not return the created object body on POST;
        # fetch it back to return a canonical representation.
        return await self.get(obj.name)

    async def update(self, name: str, obj: AddressObject) -> AddressObject:
        """Update an existing IPv4 address object.

        Args:
            name: Current name of the object (used in the URL path).
            obj: Updated object. The name in the object may differ if renaming.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        await self._put(f"{self._BASE}/name/{encoded_name}", obj.to_api_dict())
        return await self.get(obj.name)

    async def delete(self, name: str) -> None:
        """Delete an IPv4 address object by name.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        await self._delete(f"{self._BASE}/name/{encoded_name}")

    async def ensure(self, obj: AddressObject) -> tuple[AddressObject, bool]:
        """Create or update an address object (upsert).

        Returns:
            A tuple of (address_object, created) where ``created`` is True if
            the object was newly created, or False if it was updated.
        """
        try:
            existing = await self.get(obj.name)
            # Object exists — update it
            updated = await self.update(obj.name, obj)
            return updated, False
        except NotFoundError:
            # Object does not exist — create it
            created = await self.create(obj)
            return created, True