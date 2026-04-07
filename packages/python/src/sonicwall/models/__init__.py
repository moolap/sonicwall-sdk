"""SonicWall SDK model classes."""

from .access_rule import AccessRule, AccessRuleAction, RuleAddress, RulePriority, RuleService
from .address_object import AddressObject, AddressObjectType
from .dhcp import DhcpLease
from .interface import Interface, IPAssignment
from .nat_policy import NatPolicy
from .service_object import IcmpSpec, PortRange, ServiceObject, ServiceProtocol

__all__ = [
    # Address objects
    "AddressObject",
    "AddressObjectType",
    # Access rules
    "AccessRule",
    "AccessRuleAction",
    "RuleAddress",
    "RulePriority",
    "RuleService",
    # Interfaces
    "Interface",
    "IPAssignment",
    # NAT policies
    "NatPolicy",
    # Service objects
    "ServiceObject",
    "ServiceProtocol",
    "PortRange",
    "IcmpSpec",
    # DHCP
    "DhcpLease",
]