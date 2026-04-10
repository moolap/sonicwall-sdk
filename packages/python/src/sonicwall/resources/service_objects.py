"""ServiceObjects resource — full CRUD for SonicOS service objects."""

from __future__ import annotations

import logging
import urllib.parse
from typing import TYPE_CHECKING, Any

from .._exceptions import NotFoundError, SonicWallHTTPError
from ..models.service_object import ServiceObject
from ._base import BaseResource
from ._normalize import normalize_get_from_plural

if TYPE_CHECKING:
    from .._client import SonicWallClient

logger = logging.getLogger(__name__)


class ServiceObjectsResource(BaseResource):
    """CRUD operations for SonicOS service objects.

    Endpoint base: ``/service-objects``
    """

    _BASE = "/service-objects"

    def __init__(self, client: SonicWallClient) -> None:
        super().__init__(client)

    @staticmethod
    def _to_collection_payload(obj: ServiceObject) -> dict[str, Any]:
        single = obj.to_api_dict()
        item = single.get("service_object", {})
        return {"service_objects": [item]}

    @staticmethod
    def _to_firmware_collection_payload(obj: ServiceObject) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": obj.name}
        if obj.protocol.tcp:
            payload["tcp"] = {"begin": obj.protocol.tcp.begin, "end": obj.protocol.tcp.end}
        if obj.protocol.udp:
            payload["udp"] = {"begin": obj.protocol.udp.begin, "end": obj.protocol.udp.end}
        if obj.protocol.icmp:
            payload["icmp"] = {"type": obj.protocol.icmp.type, "code": obj.protocol.icmp.code}
        return {"service_objects": [payload]}

    @staticmethod
    def _is_schema_array_error(exc: SonicWallHTTPError) -> bool:
        msg = str(exc).lower()
        return (
            exc.status_code == 400
            and "schema validation error" in msg
            and "service_objects" in msg
            and "expected '['" in msg
        )

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
        try:
            response = await self._get(f"{self._BASE}/name/{encoded_name}")
            response = self._normalize_get_response(response, name=name)
            return ServiceObject.from_api_response(response)
        except NotFoundError:
            pass

        for obj in await self.list():
            if obj.name == name:
                return obj
        raise NotFoundError(status_code=404, message=f"Service object not found: {name}")

    @staticmethod
    def _normalize_get_response(response: dict[str, Any], *, name: str) -> dict[str, Any]:
        return normalize_get_from_plural(
            response,
            plural_key="service_objects",
            singular_key="service_object",
            predicate=lambda item: (
                (
                    isinstance(item.get("service_object"), dict)
                    and item["service_object"].get("name") == name
                )
                or item.get("name") == name
            ),
        )

    async def create(self, obj: ServiceObject) -> ServiceObject:
        """Create a new service object.

        Raises:
            ConflictError: if an object with the same name already exists.
        """
        payload = obj.to_api_dict()
        try:
            await self._post(self._BASE, payload)
        except SonicWallHTTPError as exc:
            if not self._is_schema_array_error(exc):
                raise
            try:
                await self._post(self._BASE, self._to_collection_payload(obj))
            except Exception:
                await self._post(self._BASE, self._to_firmware_collection_payload(obj))
        try:
            return await self.get(obj.name)
        except Exception as exc:
            logger.warning(
                "Create succeeded but service-object get parse failed; returning input object: %s",
                exc,
            )
            return obj

    async def update(self, name: str, obj: ServiceObject) -> ServiceObject:
        """Update an existing service object.

        Raises:
            NotFoundError: if the object does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        path = f"{self._BASE}/name/{encoded_name}"
        payload = obj.to_api_dict()
        try:
            await self._put(path, payload)
        except SonicWallHTTPError as exc:
            if not self._is_schema_array_error(exc):
                raise
            try:
                await self._put(path, self._to_collection_payload(obj))
            except Exception:
                await self._put(path, self._to_firmware_collection_payload(obj))
        try:
            return await self.get(obj.name)
        except Exception as exc:
            logger.warning(
                "Update succeeded but service-object get parse failed; returning input object: %s",
                exc,
            )
            return obj

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
