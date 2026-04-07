"""ServiceObjects resource — full CRUD for SonicOS service objects."""

from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING

from ..models.service_object import ServiceObject
from ._base import BaseResource
from .._exceptions import NotFoundError

if TYPE_CHECKING:
    from .._client import SonicWallClient


class ServiceObjectsResource(BaseResource):
    """CRUD operations for SonicOS service objects.

    Endpoint base: ``/service-objects``
    """

    _BASE = "/service-objects"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

    async def list(self) -> list[ServiceObject]:
        """Return all service objects."""
        return await self._list(
            self._BASE,
            list_key="service_objects",
            item_key="service_object",
            model_class=ServiceObject,
        )

    async def get(self, name: str) -> ServiceObject:
        """Fetch a service object by name.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        response = await self._get(f"{self._BASE}/name/{encoded_name}")
        return ServiceObject.from_api_response(response)

    async def create(self, obj: ServiceObject) -> ServiceObject:
        """Create a new service object.

        Raises:
            ConflictError: if an object with the same name already exists.
        """
        await self._post(self._BASE, obj.to_api_dict())
        return await self.get(obj.name)

    async def update(self, name: str, obj: ServiceObject) -> ServiceObject:
        """Update an existing service object.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        await self._put(f"{self._BASE}/name/{encoded_name}", obj.to_api_dict())
        return await self.get(obj.name)

    async def delete(self, name: str) -> None:
        """Delete a service object by name.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        await self._delete(f"{self._BASE}/name/{encoded_name}")

    async def ensure(self, obj: ServiceObject) -> tuple[ServiceObject, bool]:
        """Create or update a service object (upsert).

        Returns:
            A tuple of (service_object, created).
        """
        try:
            await self.get(obj.name)
            updated = await self.update(obj.name, obj)
            return updated, False
        except NotFoundError:
            created = await self.create(obj)
            return created, True