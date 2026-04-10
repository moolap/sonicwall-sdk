"""AddressObjects resource — full CRUD for IPv4 address objects."""

from __future__ import annotations

import logging
import urllib.parse
from typing import TYPE_CHECKING, Any

from .._exceptions import NotFoundError, SonicWallHTTPError
from ..models.address_object import AddressObject
from ._normalize import normalize_get_from_plural, unwrap_ipv4
from ._base import BaseResource

if TYPE_CHECKING:
    from .._client import SonicWallClient

logger = logging.getLogger(__name__)


class AddressObjectsResource(BaseResource):
    """CRUD operations for SonicOS IPv4 address objects.

    Endpoint base: ``/address-objects/ipv4``
    """

    _BASE = "/address-objects/ipv4"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

    @staticmethod
    def _to_collection_payload(obj: AddressObject) -> dict:
        """Build firmware-variant payload expected as address_objects array."""
        single = obj.to_api_dict()
        item = single.get("address_object", {})
        return {"address_objects": [item]}

    @staticmethod
    def _is_schema_array_error(exc: SonicWallHTTPError) -> bool:
        msg = str(exc).lower()
        return (
            exc.status_code == 400
            and "schema validation error" in msg
            and "address_objects" in msg
            and "expected '['" in msg
        )

    async def list(self) -> list[AddressObject]:
        """Return all IPv4 address objects."""
        return await self._list(
            self._BASE,
            list_key="address_objects",
            item_key="address_object",
            model_class=AddressObject,
            skip_parse_errors=True,
        )

    async def get(self, name: str) -> AddressObject:
        """Fetch a single address object by name.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        response = await self._get(f"{self._BASE}/name/{encoded_name}")
        response = self._normalize_get_response(response, expected_name=name)
        return AddressObject.from_api_response(response)

    @staticmethod
    def _normalize_get_response(response: dict[str, Any], *, expected_name: str) -> dict[str, Any]:
        """Normalize firmware-variant single-object get responses.

        Some devices return GET-by-name as {"address_objects": [ ... ]} instead
        of a direct {"address_object": ...} envelope.
        """
        return normalize_get_from_plural(
            response,
            plural_key="address_objects",
            singular_key="address_object",
            predicate=lambda item: (
                (ipv4 := unwrap_ipv4(item, "address_object")) is not None
                and ipv4.get("name") == expected_name
            ),
        )

    async def create(self, obj: AddressObject) -> AddressObject:
        """Create a new IPv4 address object.

        Raises:
            ConflictError: if an object with the same name already exists.
        """
        payload = obj.to_api_dict()
        try:
            await self._post(self._BASE, payload)
        except SonicWallHTTPError as exc:
            if not self._is_schema_array_error(exc):
                raise
            await self._post(self._BASE, self._to_collection_payload(obj))
        # SonicOS may not return stable get-by-name envelopes on all firmware.
        try:
            return await self.get(obj.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Create succeeded but get-by-name parse failed; returning input object: %s", exc)
            return obj

    async def update(self, name: str, obj: AddressObject) -> AddressObject:
        """Update an existing IPv4 address object.

        Args:
            name: Current name of the object (used in the URL path).
            obj: Updated object. The name in the object may differ if renaming.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        payload = obj.to_api_dict()
        try:
            await self._put(f"{self._BASE}/name/{encoded_name}", payload)
        except SonicWallHTTPError as exc:
            if not self._is_schema_array_error(exc):
                raise
            await self._put(
                f"{self._BASE}/name/{encoded_name}",
                self._to_collection_payload(obj),
            )
        try:
            return await self.get(obj.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Update succeeded but get-by-name parse failed; returning input object: %s", exc)
            return obj

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