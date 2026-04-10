"""DHCP lease model for SonicOS DHCP server."""

from __future__ import annotations

import ipaddress
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DhcpLease(BaseModel):
    """An active DHCP lease from the SonicOS DHCP server.

    This is a read-only object returned from the DHCP lease endpoint.
    """

    ip: ipaddress.IPv4Address = Field(..., description="Leased IP address")
    mac: str = Field(..., description="Client MAC address")
    hostname: str | None = Field(default=None, description="Client hostname if reported")
    expires: datetime | None = Field(default=None, description="Lease expiry time")
    interface: str | None = Field(default=None, description="Interface the lease was issued on")

    model_config = {"populate_by_name": True}

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "DhcpLease":
        """Parse from a SonicOS API response."""
        return cls.model_validate(
            {
                "ip": data.get("ip"),
                "mac": data.get("mac", ""),
                "hostname": data.get("hostname"),
                "expires": data.get("expires"),
                "interface": data.get("interface"),
            }
        )
