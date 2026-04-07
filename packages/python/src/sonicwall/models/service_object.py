"""ServiceObject model for SonicOS service objects."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PortRange(BaseModel):
    """TCP or UDP port range."""

    begin: int = Field(..., ge=0, le=65535)
    end: int = Field(..., ge=0, le=65535)

    @classmethod
    def single(cls, port: int) -> "PortRange":
        return cls(begin=port, end=port)


class IcmpSpec(BaseModel):
    """ICMP type/code specification."""

    type: int = Field(..., ge=0, le=255)
    code: int = Field(default=0, ge=0, le=255)


class ServiceProtocol(BaseModel):
    """Protocol specification for a service object."""

    tcp: PortRange | None = None
    udp: PortRange | None = None
    icmp: IcmpSpec | None = None


class ServiceObject(BaseModel):
    """SonicOS service object.

    SonicOS wire format envelope::

        {
          "service_object": {
            "name": "HTTPS",
            "protocol": {
              "tcp": {"begin": 443, "end": 443}
            }
          }
        }
    """

    name: str = Field(..., max_length=31)
    protocol: ServiceProtocol

    model_config = {"populate_by_name": True}

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize to the SonicOS wire format envelope."""
        proto: dict[str, Any] = {}
        if self.protocol.tcp:
            proto["tcp"] = {"begin": self.protocol.tcp.begin, "end": self.protocol.tcp.end}
        if self.protocol.udp:
            proto["udp"] = {"begin": self.protocol.udp.begin, "end": self.protocol.udp.end}
        if self.protocol.icmp:
            proto["icmp"] = {"type": self.protocol.icmp.type, "code": self.protocol.icmp.code}

        return {
            "service_object": {
                "name": self.name,
                "protocol": proto,
            }
        }

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ServiceObject":
        """Parse from a SonicOS API response."""
        if "service_object" in data:
            data = data["service_object"]

        raw_proto = data.get("protocol", {})
        proto = ServiceProtocol(
            tcp=PortRange(**raw_proto["tcp"]) if "tcp" in raw_proto else None,
            udp=PortRange(**raw_proto["udp"]) if "udp" in raw_proto else None,
            icmp=IcmpSpec(**raw_proto["icmp"]) if "icmp" in raw_proto else None,
        )
        return cls(name=data["name"], protocol=proto)