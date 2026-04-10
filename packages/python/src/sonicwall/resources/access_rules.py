"""AccessRules resource — full CRUD for IPv4 access rules."""

from __future__ import annotations

import logging
import urllib.parse
from typing import TYPE_CHECKING, Any

from .._exceptions import NotFoundError, SonicWallHTTPError
from ..models.access_rule import AccessRule
from ._base import BaseResource
from ._normalize import normalize_get_from_plural, unwrap_ipv4

if TYPE_CHECKING:
    from .._client import SonicWallClient

logger = logging.getLogger(__name__)


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

    def __init__(self, client: SonicWallClient) -> None:
        super().__init__(client)

    @staticmethod
    def _to_collection_payload(rule: AccessRule) -> dict[str, Any]:
        single = rule.to_api_dict()
        item = single.get("access_rule", {})
        return {"access_rules": [item]}

    @staticmethod
    def _is_schema_array_error(exc: SonicWallHTTPError) -> bool:
        msg = str(exc).lower()
        return (
            exc.status_code == 400
            and "schema validation error" in msg
            and "access_rules" in msg
            and "expected '['" in msg
        )

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
        path = f"{self._BASE}/from/{from_enc}/to/{to_enc}/name/{name_enc}"
        try:
            response = await self._get(path)
            response = self._normalize_get_response(
                response, from_zone=from_zone, to_zone=to_zone, name=name
            )
            return AccessRule.from_api_response(response)
        except NotFoundError:
            pass
        except SonicWallHTTPError as exc:
            if exc.status_code != 404:
                raise

        rules = await self.list()
        for rule in rules:
            if rule.from_zone == from_zone and rule.to_zone == to_zone and rule.name == name:
                return rule
        raise NotFoundError(
            status_code=404, message=f"Access rule not found: {from_zone}->{to_zone}:{name}"
        )

    @staticmethod
    def _normalize_get_response(
        response: dict[str, Any], *, from_zone: str, to_zone: str, name: str
    ) -> dict[str, Any]:
        return normalize_get_from_plural(
            response,
            plural_key="access_rules",
            singular_key="access_rule",
            predicate=lambda item: (
                (ipv4 := unwrap_ipv4(item, "access_rule")) is not None
                and ipv4.get("from") == from_zone
                and ipv4.get("to") == to_zone
                and ipv4.get("name") == name
            ),
        )

    async def create(self, rule: AccessRule) -> AccessRule:
        """Create a new access rule.

        The rule will be placed according to its priority setting.
        Use insert_before / insert_after for fine-grained ordering.

        Raises:
            ConflictError: if a rule with the same name already exists in the zone pair.
        """
        payload = rule.to_api_dict()
        try:
            await self._post(self._BASE, payload)
        except SonicWallHTTPError as exc:
            if not self._is_schema_array_error(exc):
                raise
            await self._post(self._BASE, self._to_collection_payload(rule))
        if rule.name:
            try:
                return await self.get(rule.from_zone, rule.to_zone, rule.name)
            except Exception as exc:
                logger.warning(
                    "Create succeeded but access-rule get parse failed; returning input rule: %s",
                    exc,
                )
        return rule

    async def update(self, from_zone: str, to_zone: str, name: str, rule: AccessRule) -> AccessRule:
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
        path = f"{self._BASE}/from/{from_enc}/to/{to_enc}/name/{name_enc}"
        payload = rule.to_api_dict()
        try:
            await self._put(path, payload)
        except SonicWallHTTPError as exc:
            if not self._is_schema_array_error(exc):
                raise
            await self._put(path, self._to_collection_payload(rule))
        effective_name = rule.name or name
        try:
            return await self.get(rule.from_zone, rule.to_zone, effective_name)
        except Exception as exc:
            logger.warning(
                "Update succeeded but access-rule get parse failed; returning input rule: %s", exc
            )
            return rule

    async def delete(self, from_zone: str, to_zone: str, name: str) -> None:
        """Delete an access rule by zone pair and name.

        Raises:
            NotFoundError: if the rule does not exist.
        """
        from_enc = urllib.parse.quote(from_zone, safe="")
        to_enc = urllib.parse.quote(to_zone, safe="")
        name_enc = urllib.parse.quote(name, safe="")
        await self._delete(f"{self._BASE}/from/{from_enc}/to/{to_enc}/name/{name_enc}")

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
                    update={"priority": RulePriority(auto=False, value=target.priority.value + 1)}
                )
        except NotFoundError:
            pass
        return await self.create(rule)
