# Python SDK — Getting Started

## Requirements

- Python 3.10+
- `uv` or `pip`

## Installation

```bash
pip install sonicwall-sdk
# or:
uv add sonicwall-sdk
```

## Async usage (recommended)

```python
import asyncio
from sonicwall import SonicWallClient
from sonicwall.models import AddressObject, AddressObjectType

async def main():
    async with SonicWallClient(
        host="192.168.1.1",
        username="admin",
        password="secret",
        verify_ssl=False,   # default — most SonicWalls use self-signed certs
        timeout=30.0,
    ) as client:
        # List all IPv4 address objects
        objects = await client.address_objects.list()
        for obj in objects:
            print(obj.name, obj.type.value)

        # Get a specific object
        server = await client.address_objects.get("web-server")
        print(server.host)

        # Create a new host object
        new_obj = AddressObject(
            name="my-server",
            type=AddressObjectType.HOST,
            host="10.0.0.100",
            zone="LAN",
        )
        created = await client.address_objects.create(new_obj)
        print(created.name)

asyncio.run(main())
```

## Sync usage

```python
from sonicwall import SonicWallClientSync
from sonicwall.models import AddressObject, AddressObjectType

with SonicWallClientSync("192.168.1.1", "admin", "secret") as client:
    objects = client.address_objects.list()
    print(f"{len(objects)} address objects")
```

## Pending-config transactions

SonicOS stages write operations in a pending queue. You must commit to make
changes persistent, or roll back to discard them. Use the `pending()` context
manager:

```python
async with client.pending():
    await client.address_objects.create(obj1)
    await client.nat_policies.create(policy)
    # On clean exit: automatically commits
    # On exception: automatically rolls back
```

You can also commit/rollback manually:

```python
await client.address_objects.create(obj)
await client.commit()     # or await client.rollback()
```

## Error handling

```python
from sonicwall import (
    NotFoundError,
    ConflictError,
    AuthenticationError,
    SessionExpiredError,
    CommitError,
)

try:
    obj = await client.address_objects.get("doesnt-exist")
except NotFoundError:
    print("Not found")
except ConflictError as e:
    print(f"Already exists: {e.sonicos_message}")
except SessionExpiredError:
    # SDK re-authenticates automatically, but if it keeps failing:
    print("Session could not be renewed")
except CommitError as e:
    print(f"Commit failed: {e}")
```

## Upsert (ensure)

```python
# Create if missing, update if exists
obj, was_created = await client.address_objects.ensure(
    AddressObject(name="my-server", type=AddressObjectType.HOST, host="10.0.0.100", zone="LAN")
)
print("Created" if was_created else "Updated")
```

## Access rules

```python
from sonicwall.models import AccessRule, AccessRuleAction, RuleAddress, RuleService

rule = AccessRule(
    **{"from": "WAN", "to": "LAN"},
    action=AccessRuleAction.DENY,
    name="block-telnet",
    service=RuleService(name="Telnet"),
)
async with client.pending():
    await client.access_rules.create(rule)
```

## NAT policies

```python
from sonicwall.models import NatPolicy

policy = NatPolicy(
    name="outbound-nat",
    inbound_interface="any",
    outbound_interface="X1",
    original_source="LAN Subnets",
    translated_source="interface ip",
)
async with client.pending():
    await client.nat_policies.create(policy)
```

## Interfaces (read-only)

```python
interfaces = await client.interfaces.list()
for iface in interfaces:
    print(iface.name, iface.ip, iface.zone)

x0 = await client.interfaces.get("X0")
print(x0.network)   # IPv4Network object
```

## DHCP leases

```python
leases = await client.dhcp.list_leases()
for lease in leases:
    print(lease.ip, lease.mac, lease.hostname)
```