"""NatPolicies resource — full CRUD for IPv4 NAT policies."""

from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING

from ..models.nat_policy import NatPolicy
from ._base import BaseResource
from .._exceptions import NotFoundError

if TYPE_CHECKING:
    from .._client import SonicWallClient


class NatPoliciesResource(BaseResource):
    """CRUD operations for SonicOS IPv4 NAT policies.

    Endpoint base: ``/nat-policies/ipv4``
    """

    _BASE = "/nat-policies/ipv4"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

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
        response = await self._get(f"{self._BASE}/name/{encoded_name}")
        return NatPolicy.from_api_response(response)

    async def create(self, policy: NatPolicy) -> NatPolicy:
        """Create a new NAT policy.

        Raises:
            ConflictError: if a policy with the same name already exists.
        """
        await self._post(self._BASE, policy.to_api_dict())
        if policy.name:
            return await self.get(policy.name)
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
        await self._put(f"{self._BASE}/name/{encoded_name}", policy.to_api_dict())
        effective_name = policy.name or name
        return await self.get(effective_name)

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