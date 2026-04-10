"""NatPolicies resource — full CRUD for IPv4 NAT policies."""

from __future__ import annotations

import logging
import urllib.parse
from typing import TYPE_CHECKING, Any

from .._exceptions import NotFoundError
from ..models.nat_policy import NatPolicy
from ._base import BaseResource
from ._normalize import normalize_get_from_plural, unwrap_ipv4

if TYPE_CHECKING:
    from .._client import SonicWallClient

logger = logging.getLogger(__name__)


class NatPoliciesResource(BaseResource):
    """CRUD operations for SonicOS IPv4 NAT policies.

    Endpoint base: ``/nat-policies/ipv4``
    """

    _BASE = "/nat-policies/ipv4"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

    @staticmethod
    def _to_collection_payload(policy: NatPolicy) -> dict[str, Any]:
        single = policy.to_api_dict()
        item = single.get("nat_policy", {})
        return {"nat_policies": [item]}

    @staticmethod
    def _ref_obj(value: str, *, allow_original: bool = False) -> dict[str, Any]:
        if value == "any":
            return {"any": True}
        if allow_original and value == "original":
            return {"original": True}
        return {"name": value}

    @classmethod
    def _to_firmware_collection_payload(cls, policy: NatPolicy) -> dict[str, Any]:
        return {
            "nat_policies": [
                {
                    "ipv4": {
                        "name": policy.name,
                        "inbound": policy.inbound_interface,
                        "outbound": policy.outbound_interface,
                        "source": cls._ref_obj(policy.original_source),
                        "translated_source": cls._ref_obj(policy.translated_source, allow_original=True),
                        "destination": cls._ref_obj(policy.original_destination),
                        "translated_destination": cls._ref_obj(
                            policy.translated_destination, allow_original=True
                        ),
                        "service": cls._ref_obj(policy.original_service),
                        "translated_service": cls._ref_obj(
                            policy.translated_service, allow_original=True
                        ),
                        "enable": policy.enabled,
                        "comment": policy.comment or "",
                    }
                }
            ]
        }

    @staticmethod
    def _is_schema_array_error(exc: Exception) -> bool:
        if not hasattr(exc, "status_code"):
            return False
        msg = str(exc).lower()
        return (
            getattr(exc, "status_code", None) == 400
            and "schema validation error" in msg
            and "nat_policies" in msg
            and "expected '['" in msg
        )

    async def list(self) -> list[NatPolicy]:
        """Return all IPv4 NAT policies."""
        return await self._list(
            self._BASE,
            list_key="nat_policies",
            item_key="nat_policy",
            model_class=NatPolicy,
        )

    async def get(self, name: str) -> NatPolicy:
        """Fetch a NAT policy by name.

        Raises:
            NotFoundError: if the policy does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        try:
            response = await self._get(f"{self._BASE}/name/{encoded_name}")
            response = self._normalize_get_response(response, name=name)
            return NatPolicy.from_api_response(response)
        except NotFoundError:
            pass

        for policy in await self.list():
            if policy.name == name:
                return policy
        raise NotFoundError(status_code=404, message=f"NAT policy not found: {name}")

    @staticmethod
    def _normalize_get_response(response: dict[str, Any], *, name: str) -> dict[str, Any]:
        return normalize_get_from_plural(
            response,
            plural_key="nat_policies",
            singular_key="nat_policy",
            predicate=lambda item: (
                (ipv4 := unwrap_ipv4(item, "nat_policy")) is not None
                and ipv4.get("name") == name
            ),
        )

    async def create(self, policy: NatPolicy) -> NatPolicy:
        """Create a new NAT policy.

        Raises:
            ConflictError: if a policy with the same name already exists.
        """
        payload = policy.to_api_dict()
        try:
            await self._post(self._BASE, payload)
        except Exception as exc:  # noqa: BLE001
            if not self._is_schema_array_error(exc):
                raise
            try:
                await self._post(self._BASE, self._to_collection_payload(policy))
            except Exception:
                await self._post(self._BASE, self._to_firmware_collection_payload(policy))
        if policy.name:
            try:
                return await self.get(policy.name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Create succeeded but NAT get parse failed; returning input policy: %s", exc)
        return policy

    async def update(self, name: str, policy: NatPolicy) -> NatPolicy:
        """Update an existing NAT policy.

        Args:
            name: Current name of the policy.
            policy: Updated policy object.

        Raises:
            NotFoundError: if the policy does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        path = f"{self._BASE}/name/{encoded_name}"
        payload = policy.to_api_dict()
        try:
            await self._put(path, payload)
        except Exception as exc:  # noqa: BLE001
            if not self._is_schema_array_error(exc):
                raise
            try:
                await self._put(path, self._to_collection_payload(policy))
            except Exception:
                await self._put(path, self._to_firmware_collection_payload(policy))
        effective_name = policy.name or name
        try:
            return await self.get(effective_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Update succeeded but NAT get parse failed; returning input policy: %s", exc)
            return policy

    async def delete(self, name: str) -> None:
        """Delete a NAT policy by name.

        Raises:
            NotFoundError: if the policy does not exist.
        """
        encoded_name = urllib.parse.quote(name, safe="")
        await self._delete(f"{self._BASE}/name/{encoded_name}")

    async def ensure(self, policy: NatPolicy) -> tuple[NatPolicy, bool]:
        """Create or update a NAT policy (upsert).

        Returns:
            A tuple of (policy, created) where ``created`` is True if
            the policy was newly created.
        """
        if not policy.name:
            created = await self.create(policy)
            return created, True
        try:
            await self.get(policy.name)
            updated = await self.update(policy.name, policy)
            return updated, False
        except NotFoundError:
            created = await self.create(policy)
            return created, True