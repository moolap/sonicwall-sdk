"""AccessRule model for SonicOS IPv4 access rules."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AccessRuleAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    DISCARD = "discard"


class RuleAddress(BaseModel):
    """Source or destination address specification for an access rule."""

    any: bool = False
    name: str | None = None
    group: str | None = None


class RuleService(BaseModel):
    """Service specification for an access rule."""

    any: bool = False
    name: str | None = None


class RulePriority(BaseModel):
    """Priority specification for an access rule."""

    auto: bool = True
    value: int | None = None


class AccessRule(BaseModel):
    """IPv4 access rule as represented in SonicOS.

    SonicOS wire format envelope::

        {
          "access_rule": {
            "ipv4": {
              "name": "block-ssh",
              "from": "WAN",
              "to": "LAN",
              "action": "deny",
              ...
            }
          }
        }
    """

    name: str | None = Field(default=None, max_length=31)
    from_zone: str = Field(..., alias="from", description="Source zone")
    to_zone: str = Field(..., alias="to", description="Destination zone")
    action: AccessRuleAction = AccessRuleAction.ALLOW
    enabled: bool = True
    log: bool = False
    priority: RulePriority = Field(default_factory=RulePriority)
    source_address: RuleAddress = Field(
        default_factory=lambda: RuleAddress(any=True), alias="source"
    )
    destination_address: RuleAddress = Field(
        default_factory=lambda: RuleAddress(any=True), alias="destination"
    )
    service: RuleService = Field(default_factory=lambda: RuleService(any=True))
    comment: str | None = Field(default=None, max_length=255)

    model_config = {"populate_by_name": True}

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize to the SonicOS wire format envelope."""
        inner: dict[str, Any] = {
            "from": self.from_zone,
            "to": self.to_zone,
            "action": self.action.value,
            "enabled": self.enabled,
            "log": self.log,
        }

        if self.name:
            inner["name"] = self.name

        # Priority
        if self.priority.auto:
            inner["priority"] = {"auto": True}
        elif self.priority.value is not None:
            inner["priority"] = {"value": self.priority.value}

        # Source
        if self.source_address.any:
            inner["source"] = {"address": {"any": True}}
        elif self.source_address.name:
            inner["source"] = {"address": {"name": self.source_address.name}}
        elif self.source_address.group:
            inner["source"] = {"address": {"group": self.source_address.group}}

        # Destination
        if self.destination_address.any:
            inner["destination"] = {"address": {"any": True}}
        elif self.destination_address.name:
            inner["destination"] = {"address": {"name": self.destination_address.name}}
        elif self.destination_address.group:
            inner["destination"] = {"address": {"group": self.destination_address.group}}

        # Service
        if self.service.any:
            inner["service"] = {"any": True}
        elif self.service.name:
            inner["service"] = {"name": self.service.name}

        if self.comment:
            inner["comment"] = self.comment

        return {"access_rule": {"ipv4": inner}}

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "AccessRule":
        """Parse from a SonicOS API response."""
        if "access_rule" in data:
            data = data["access_rule"]
        if "ipv4" in data:
            data = data["ipv4"]

        kwargs: dict[str, Any] = {
            "from": data.get("from", ""),
            "to": data.get("to", ""),
            "action": data.get("action", "allow"),
            "enabled": data.get("enabled", True),
            "log": data.get("log", False),
            "name": data.get("name"),
            "comment": data.get("comment"),
        }

        # Priority
        prio = data.get("priority", {})
        if isinstance(prio, dict):
            if prio.get("auto"):
                kwargs["priority"] = RulePriority(auto=True)
            elif "value" in prio:
                kwargs["priority"] = RulePriority(auto=False, value=prio["value"])

        # Source address
        src = data.get("source", {}).get("address", {})
        if src.get("any"):
            kwargs["source"] = RuleAddress(any=True)
        elif src.get("name"):
            kwargs["source"] = RuleAddress(name=src["name"])
        elif src.get("group"):
            kwargs["source"] = RuleAddress(group=src["group"])

        # Destination address
        dst = data.get("destination", {}).get("address", {})
        if dst.get("any"):
            kwargs["destination"] = RuleAddress(any=True)
        elif dst.get("name"):
            kwargs["destination"] = RuleAddress(name=dst["name"])
        elif dst.get("group"):
            kwargs["destination"] = RuleAddress(group=dst["group"])

        # Service
        svc = data.get("service", {})
        if isinstance(svc, dict):
            if svc.get("any"):
                kwargs["service"] = RuleService(any=True)
            elif svc.get("name"):
                kwargs["service"] = RuleService(name=svc["name"])

        return cls.model_validate(kwargs)