"""AccessRules resource — full CRUD for IPv4 access rules."""

from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING

from ..models.access_rule import AccessRule
from ._base import BaseResource
from .._exceptions import NotFoundError

if TYPE_CHECKING:
    from .._client import SonicWallClient


class AccessRulesResource(BaseResource):
    """CRUD operations for SonicOS IPv4 access rules.

    Endpoint base: ``/access-rules/ipv4``

    Note on SonicOS access rule ordering:
        SonicOS evaluates access rules top-down, first match wins.
        The API does not expose a simple "insert at position N" operation.
        Use ``insert_before`` / ``insert_after`` to control ordering relative
        to named rules. The priority field (auto vs. value) determines where
        new rules are placed when auto=True.
    """

    _BASE = "/access-rules/ipv4"

    def __init__(self, client: "SonicWallClient") -> None:
        super().__init__(client)

    async def list(self) -> list[AccessRule]:
        """Return all IPv4 access rules."""
        return await self._list(
            self._BASE,
            list_key="access_rules",
            item_key="access_rule",
            model_class=AccessRule,
        )

    async def get(self, from_zone: str, to_zone: str, name: str) -> AccessRule:
        """Fetch a specific access rule by zone pair and name.

        Args:
            from_zone: Source zone name (e.g. "WAN")
            to_zone: Destination zone name (e.g. "LAN")
            name: Rule name

        Raises:
            NotFoundError: if the rule does not exist.
        """
        from_enc = urllib.parse.quote(from_zone, safe="")
        to_enc = urllib.parse.quote(to_zone, safe="")
        name_enc = urllib.parse.quote(name, safe="")
        response = await self._get(
            f"{self._BASE}/from/{from_enc}/to/{to_enc}/name/{name_enc}"
        )
        return AccessRule.from_api_response(response)

    async def create(self, rule: AccessRule) -> AccessRule:
        """Create a new access rule.

        The rule will be placed according to its priority setting.
        Use insert_before / insert_after for fine-grained ordering.

        Raises:
            ConflictError: if a rule with the same name already exists in the zone pair.
        """
        await self._post(self._BASE, rule.to_api_dict())
        if rule.name:
            return await self.get(rule.from_zone, rule.to_zone, rule.name)
        return rule

    async def update(
        self, from_zone: str, to_zone: str, name: str, rule: AccessRule
    ) -> AccessRule:
        """Update an existing access rule.

        Args:
            from_zone: Source zone of the existing rule.
            to_zone: Destination zone of the existing rule.
            name: Name of the existing rule.
            rule: Updated rule object.

        Raises:
            NotFoundError: if the rule does not exist.
        """
        from_enc = urllib.parse.quote(from_zone, safe="")
        to_enc = urllib.parse.quote(to_zone, safe="")
        name_enc = urllib.parse.quote(name, safe="")
        await self._put(
            f"{self._BASE}/from/{from_enc}/to/{to_enc}/name/{name_enc}",
            rule.to_api_dict(),
        )
        effective_name = rule.name or name
        return await self.get(rule.from_zone, rule.to_zone, effective_name)

    async def delete(self, from_zone: str, to_zone: str, name: str) -> None:
        """Delete an access rule by zone pair and name.

        Raises:
            NotFoundError: if the rule does not exist.
        """
        from_enc = urllib.parse.quote(from_zone, safe="")
        to_enc = urllib.parse.quote(to_zone, safe="")
        name_enc = urllib.parse.quote(name, safe="")
        await self._delete(
            f"{self._BASE}/from/{from_enc}/to/{to_enc}/name/{name_enc}"
        )

    async def insert_before(self, rule: AccessRule, before_name: str) -> AccessRule:
        """Insert a new access rule immediately before the named existing rule.

        This sets the rule priority to place it above ``before_name`` in the
        rule ordering. SonicOS uses priority values where lower values run first;
        this method reads the target rule's priority and sets the new rule's
        priority to (target priority - 1).

        If the target rule uses auto-priority, this falls back to regular create.

        Args:
            rule: The new rule to insert. Must have from_zone and to_zone set.
            before_name: Name of the existing rule to insert before.

        Returns:
            The created rule.
        """
        try:
            target = await self.get(rule.from_zone, rule.to_zone, before_name)
            if not target.priority.auto and target.priority.value is not None:
                from ..models.access_rule import RulePriority
                rule = rule.model_copy(
                    update={"priority": RulePriority(auto=False, value=target.priority.value)}
                )
        except NotFoundError:
            pass  # Fall through to regular create
        return await self.create(rule)

    async def insert_after(self, rule: AccessRule, after_name: str) -> AccessRule:
        """Insert a new access rule immediately after the named existing rule.

        Args:
            rule: The new rule to insert. Must have from_zone and to_zone set.
            after_name: Name of the existing rule to insert after.

        Returns:
            The created rule.
        """
        try:
            target = await self.get(rule.from_zone, rule.to_zone, after_name)
            if not target.priority.auto and target.priority.value is not None:
                from ..models.access_rule import RulePriority
                rule = rule.model_copy(
                    update={
                        "priority": RulePriority(auto=False, value=target.priority.value + 1)
                    }
                )
        except NotFoundError:
            pass
        return await self.create(rule)