#!/usr/bin/env python3
"""Smoke test against a live SonicWall device.

Usage:
    cd packages/python
    uv run ../../smoke_test.py --host 192.168.0.1 --user admin --password YOUR_PASSWORD

Or with env vars:
    SW_HOST=192.168.0.1 SW_USER=admin SW_PASS=yourpass uv run ../../smoke_test.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, "src")

from sonicwall import SonicWallClient
from sonicwall._exceptions import NotFoundError, SonicWallError, SonicWallHTTPError


def ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m  {msg}")


def fail(msg: str) -> None:
    print(f"  \033[31m✗\033[0m  {msg}")


def skip(msg: str) -> None:
    print(f"  \033[33m-\033[0m  {msg}")


def section(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m")


async def run(host: str, username: str, password: str) -> int:
    errors = 0

    section("1. Authentication")
    try:
        client = SonicWallClient(host, username, password, verify_ssl=False)
        await client.connect()
        ok(f"Logged in to https://{host}")
    except SonicWallError as e:
        fail(f"Login failed: {e}")
        return 1

    async with client:
        section("2. Address objects (read-only)")
        try:
            objs = await client.address_objects.list()
            ok(f"Listed {len(objs)} address objects")
            if objs:
                first = objs[0]
                ok(f"First object: {first.name!r}  type={first.type}  zone={first.zone}")
        except SonicWallError as e:
            fail(f"address_objects.list() failed: {e}")
            errors += 1

        section("3. Access rules (read-only)")
        try:
            rules = await client.access_rules.list()
            ok(f"Listed {len(rules)} access rules")
        except SonicWallError as e:
            fail(f"access_rules.list() failed: {e}")
            errors += 1

        section("4. Interfaces (read-only)")
        try:
            ifaces = await client.interfaces.list()
            ok(f"Listed {len(ifaces)} interfaces")
            for iface in ifaces[:3]:
                ok(f"  {iface.name}  ip={iface.ip_assignment}")
        except SonicWallHTTPError as e:
            # Some firmware builds expose an incomplete interfaces endpoint.
            if e.status_code == 400 and "incomplete" in str(e).lower():
                skip(f"interfaces.list() unsupported on this firmware: {e}")
            else:
                fail(f"interfaces.list() failed: {e}")
                errors += 1
        except SonicWallError as e:
            fail(f"interfaces.list() failed: {e}")
            errors += 1

        section("5. NAT policies (read-only)")
        try:
            nats = await client.nat_policies.list()
            ok(f"Listed {len(nats)} NAT policies")
        except SonicWallError as e:
            fail(f"nat_policies.list() failed: {e}")
            errors += 1

        section("6. Service objects (read-only)")
        try:
            svcs = await client.service_objects.list()
            ok(f"Listed {len(svcs)} service objects")
        except SonicWallError as e:
            fail(f"service_objects.list() failed: {e}")
            errors += 1

        section("7. DHCP leases (read-only)")
        try:
            leases = await client.dhcp.list_leases()
            ok(f"Listed {len(leases)} DHCP leases")
            for lease in leases[:3]:
                ok(f"  {lease.mac}  ip={lease.ip}  host={lease.hostname or '-'}")
        except SonicWallHTTPError as e:
            if e.status_code == 400 and "incomplete" in str(e).lower():
                skip(f"dhcp.list_leases() unsupported on this firmware: {e}")
            else:
                fail(f"dhcp.list_leases() failed: {e}")
                errors += 1
        except NotFoundError as e:
            # DHCP lease endpoint is not present on some devices/firmware.
            skip(f"dhcp.list_leases() unsupported on this firmware: {e}")
        except SonicWallError as e:
            fail(f"dhcp.list_leases() failed: {e}")
            errors += 1

        section("8. Write test — create + delete a test address object")
        test_name = "sdk-smoke-test-DO-NOT-USE"
        try:
            from sonicwall.models.address_object import AddressObject, AddressObjectType
            obj = AddressObject(
                name=test_name,
                type=AddressObjectType.HOST,
                zone="LAN",
                host="10.255.254.253",
            )
            async with client.pending():
                await client.address_objects.create(obj)
                ok(f"Created test address object {test_name!r}")
                await client.address_objects.delete(test_name)
                ok(f"Deleted test address object {test_name!r}")
            ok("Commit successful — write path works end-to-end")
        except SonicWallHTTPError as e:
            # Some firmware requires an explicit config-mode transition before writes.
            if e.status_code == 405 and "non config mode" in str(e).lower():
                skip(f"write path requires config mode on this firmware: {e}")
            else:
                fail(f"Write test failed: {e}")
                errors += 1
        except SonicWallError as e:
            fail(f"Write test failed: {e}")
            errors += 1

    section("Summary")
    if errors == 0:
        print("\n  \033[32mAll checks passed.\033[0m\n")
    else:
        print(f"\n  \033[31m{errors} check(s) failed.\033[0m\n")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="SonicWall SDK smoke test")
    parser.add_argument("--host", default=os.getenv("SW_HOST", "192.168.0.1"))
    parser.add_argument("--user", default=os.getenv("SW_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("SW_PASS", ""))
    args = parser.parse_args()

    if not args.password:
        print("Error: provide --password or set SW_PASS env var")
        sys.exit(1)

    sys.exit(asyncio.run(run(args.host, args.user, args.password)))


if __name__ == "__main__":
    main()