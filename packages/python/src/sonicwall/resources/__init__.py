"""SonicWall SDK resource classes."""

from .access_rules import AccessRulesResource
from .address_objects import AddressObjectsResource
from .dhcp import DhcpResource
from .interfaces import InterfacesResource
from .nat_policies import NatPoliciesResource
from .service_objects import ServiceObjectsResource

__all__ = [
    "AddressObjectsResource",
    "AccessRulesResource",
    "InterfacesResource",
    "NatPoliciesResource",
    "ServiceObjectsResource",
    "DhcpResource",
]
