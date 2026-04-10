"""NatPolicy model for SonicOS IPv4 NAT policies."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NatPolicy(BaseModel):
    """IPv4 NAT policy as represented in SonicOS.

    SonicOS wire format envelope::

        {
          "nat_policy": {
            "ipv4": {
              "name": "outbound-nat",
              "inbound_interface": "any",
              "outbound_interface": "X1",
              "original_source": "LAN Subnets",
              "translated_source": "interface ip",
              "original_destination": "any",
              "translated_destination": "original",
              "original_service": "any",
              "translated_service": "original",
              "enabled": true
            }
          }
        }
    """

    name: str | None = Field(default=None, max_length=31)
    enabled: bool = True
    inbound_interface: str = Field(..., description="Inbound interface name or 'any'")
    outbound_interface: str = Field(..., description="Outbound interface name or 'any'")
    original_source: str = Field(
        default="any", description="Original source address object or 'any'"
    )
    translated_source: str = Field(
        default="original",
        description="Translated source address object, 'original', or 'interface ip'",
    )
    original_destination: str = Field(
        default="any", description="Original destination address object or 'any'"
    )
    translated_destination: str = Field(
        default="original",
        description="Translated destination address object or 'original'",
    )
    original_service: str = Field(default="any", description="Original service object or 'any'")
    translated_service: str = Field(
        default="original", description="Translated service object or 'original'"
    )
    comment: str | None = Field(default=None, max_length=255)

    model_config = {"populate_by_name": True}

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize to the SonicOS wire format envelope."""
        inner: dict[str, Any] = {
            "inbound_interface": self.inbound_interface,
            "outbound_interface": self.outbound_interface,
            "original_source": self.original_source,
            "translated_source": self.translated_source,
            "original_destination": self.original_destination,
            "translated_destination": self.translated_destination,
            "original_service": self.original_service,
            "translated_service": self.translated_service,
            "enabled": self.enabled,
        }
        if self.name:
            inner["name"] = self.name
        if self.comment:
            inner["comment"] = self.comment
        return {"nat_policy": {"ipv4": inner}}

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> NatPolicy:
        """Parse from a SonicOS API response."""
        if "nat_policy" in data:
            data = data["nat_policy"]
        if "ipv4" in data:
            data = data["ipv4"]

        def norm_ref(value: Any, *, default: str) -> str:
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                if value.get("any"):
                    return "any"
                if value.get("original"):
                    return "original"
                for key in ("name", "group"):
                    v = value.get(key)
                    if isinstance(v, str) and v:
                        return v
            return default

        return cls.model_validate(
            {
                "name": data.get("name"),
                "enabled": data.get("enabled", data.get("enable", True)),
                "inbound_interface": data.get("inbound_interface", data.get("inbound", "any")),
                "outbound_interface": data.get("outbound_interface", data.get("outbound", "any")),
                "original_source": norm_ref(
                    data.get("original_source", data.get("source")), default="any"
                ),
                "translated_source": norm_ref(data.get("translated_source"), default="original"),
                "original_destination": norm_ref(
                    data.get("original_destination", data.get("destination")), default="any"
                ),
                "translated_destination": norm_ref(
                    data.get("translated_destination"), default="original"
                ),
                "original_service": norm_ref(
                    data.get("original_service", data.get("service")), default="any"
                ),
                "translated_service": norm_ref(data.get("translated_service"), default="original"),
                "comment": data.get("comment"),
            }
        )
