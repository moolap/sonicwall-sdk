"""SonicWall SDK — Python client for the SonicOS REST API."""

from ._client import SonicWallClient, SonicWallClientSync
from ._exceptions import (
    AuthenticationError,
    AuthorizationError,
    CommitError,
    ConflictError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    RollbackError,
    SessionExpiredError,
    SonicWallError,
    SonicWallHTTPError,
    UnsupportedEndpointError,
)
from .models import (
    AccessRule,
    AccessRuleAction,
    AddressObject,
    AddressObjectType,
    DhcpLease,
    IcmpSpec,
    Interface,
    IPAssignment,
    NatPolicy,
    PortRange,
    RuleAddress,
    RulePriority,
    RuleService,
    ServiceObject,
    ServiceProtocol,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Clients
    "SonicWallClient",
    "SonicWallClientSync",
    # Exceptions
    "SonicWallError",
    "SonicWallHTTPError",
    "AuthenticationError",
    "AuthorizationError",
    "SessionExpiredError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "CommitError",
    "RollbackError",
    "ConnectionError",
    "UnsupportedEndpointError",
    # Models
    "AddressObject",
    "AddressObjectType",
    "AccessRule",
    "AccessRuleAction",
    "RuleAddress",
    "RulePriority",
    "RuleService",
    "Interface",
    "IPAssignment",
    "NatPolicy",
    "ServiceObject",
    "ServiceProtocol",
    "PortRange",
    "IcmpSpec",
    "DhcpLease",
]
