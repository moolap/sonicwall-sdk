"""AddressObject model for SonicOS IPv4 address objects."""

from __future__ import annotations

import ipaddress
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AddressObjectType(str, Enum):
    HOST = "host"
    RANGE = "range"
    NETWORK = "network"
    FQDN = "fqdn"
    MAC = "mac"


class AddressObject(BaseModel):
    """IPv4 address object as represented in SonicOS.

    SonicOS wire format (nested envelope)::

        {
          "address_object": {
            "ipv4": {
              "name": "my-server",
              "zone": "LAN",
              "host": {"ip": "10.0.0.100"}
            }
          }
        }
    """

    name: str = Field(..., max_length=31, description="Object name, unique within zone")
    type: AddressObjectType
    zone: str = Field(default="LAN", description="Zone the object belongs to")

    # Type-specific fields — exactly one must be set based on 'type'
    host: ipaddress.IPv4Address | None = Field(
        default=None, description="Host IP address (when type=host)"
    )
    network: ipaddress.IPv4Network | None = Field(
        default=None, description="Network with prefix (when type=network)"
    )
    range_start: ipaddress.IPv4Address | None = Field(
        default=None,
        alias="range-start",
        description="Range start address (when type=range)",
    )
    range_end: ipaddress.IPv4Address | None = Field(
        default=None,
        alias="range-end",
        description="Range end address (when type=range)",
    )
    fqdn: str | None = Field(default=None, description="Fully qualified domain name (when type=fqdn)")
    mac: str | None = Field(default=None, description="MAC address (when type=mac)")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_type_fields(self) -> "AddressObject":
        """Ensure the correct field is populated for the given type."""
        if self.type == AddressObjectType.HOST and self.host is None:
            raise ValueError("'host' IP address is required when type is 'host'")
        if self.type == AddressObjectType.NETWORK and self.network is None:
            raise ValueError("'network' is required when type is 'network'")
        if self.type == AddressObjectType.RANGE and (
            self.range_start is None or self.range_end is None
        ):
            raise ValueError(
                "'range_start' and 'range_end' are required when type is 'range'"
            )
        if self.type == AddressObjectType.FQDN and not self.fqdn:
            raise ValueError("'fqdn' is required when type is 'fqdn'")
        if self.type == AddressObjectType.MAC and not self.mac:
            raise ValueError("'mac' is required when type is 'mac'")
        return self

    @field_validator("network", mode="before")
    @classmethod
    def parse_network(cls, v: Any) -> Any:
        if isinstance(v, str):
            return ipaddress.IPv4Network(v, strict=False)
        return v

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize to the SonicOS wire format envelope."""
        inner: dict[str, Any] = {
            "name": self.name,
            "zone": self.zone,
        }

        if self.type == AddressObjectType.HOST and self.host is not None:
            inner["host"] = {"ip": str(self.host)}

        elif self.type == AddressObjectType.NETWORK and self.network is not None:
            inner["network"] = {
                "subnet": str(self.network.network_address),
                "mask": str(self.network.netmask),
            }

        elif self.type == AddressObjectType.RANGE:
            inner["range"] = {
                "begin": str(self.range_start),
                "end": str(self.range_end),
            }

        elif self.type == AddressObjectType.FQDN:
            inner["fqdn"] = {"domain": self.fqdn}

        elif self.type == AddressObjectType.MAC:
            inner["mac"] = {"address": self.mac}

        return {"address_object": {"ipv4": inner}}

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "AddressObject":
        """Parse from a SonicOS API response (envelope or raw ipv4 dict)."""
        # Navigate envelope layers: {address_object: {ipv4: {...}}}
        if "address_object" in data:
            data = data["address_object"]
        if "ipv4" in data:
            data = data["ipv4"]

        # Determine type from which field is present
        obj_type: AddressObjectType
        kwargs: dict[str, Any] = {
            "name": data["name"],
            "zone": data.get("zone", "LAN"),
        }

        if "host" in data:
            obj_type = AddressObjectType.HOST
            kwargs["host"] = data["host"]["ip"]
        elif "network" in data:
            obj_type = AddressObjectType.NETWORK
            subnet = data["network"]["subnet"]
            mask = data["network"]["mask"]
            # Convert dotted-decimal mask to CIDR prefix
            net = ipaddress.IPv4Network(f"{subnet}/{mask}", strict=False)
            kwargs["network"] = net
        elif "range" in data:
            obj_type = AddressObjectType.RANGE
            kwargs["range-start"] = data["range"]["begin"]
            kwargs["range-end"] = data["range"]["end"]
        elif "fqdn" in data:
            obj_type = AddressObjectType.FQDN
            kwargs["fqdn"] = data["fqdn"]["domain"]
        elif "mac" in data:
            obj_type = AddressObjectType.MAC
            kwargs["mac"] = data["mac"]["address"]
        else:
            raise ValueError(f"Cannot determine address object type from data: {data}")

        kwargs["type"] = obj_type
        return cls.model_validate(kwargs)