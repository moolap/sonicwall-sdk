"""Interface model for SonicOS interfaces (read-only)."""

from __future__ import annotations

import ipaddress
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IPAssignment(str, Enum):
    STATIC = "static"
    DHCP = "dhcp"
    PPPOE = "pppoe"
    L2TP = "l2tp"


class Interface(BaseModel):
    """SonicOS network interface (read-only resource).

    SonicOS wire format envelope::

        {
          "interface": {
            "name": "X0",
            "ip_assignment": "static",
            "ip": "192.168.1.1",
            "subnet": "255.255.255.0",
            "zone": "LAN",
            "enabled": true
          }
        }
    """

    name: str = Field(..., description="Interface name, e.g. X0, X1, X2")
    ip_assignment: IPAssignment | None = Field(
        default=None, description="IP assignment method"
    )
    ip: ipaddress.IPv4Address | None = Field(
        default=None, description="Static IP address"
    )
    subnet: ipaddress.IPv4Address | None = Field(
        default=None, description="Subnet mask in dotted-decimal"
    )
    zone: str | None = Field(default=None, description="Zone assignment")
    enabled: bool = True
    comment: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def network(self) -> ipaddress.IPv4Network | None:
        """Return the network this interface is on, or None if unknown."""
        if self.ip and self.subnet:
            return ipaddress.IPv4Network(f"{self.ip}/{self.subnet}", strict=False)
        return None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Interface":
        """Parse from a SonicOS API response."""
        if "interface" in data:
            data = data["interface"]

        return cls.model_validate(
            {
                "name": data.get("name", ""),
                "ip_assignment": data.get("ip_assignment"),
                "ip": data.get("ip"),
                "subnet": data.get("subnet"),
                "zone": data.get("zone"),
                "enabled": data.get("enabled", True),
                "comment": data.get("comment"),
            }
        )