#!/usr/bin/env python3
"""Live firmware write CRUD validator for key resources."""

from __future__ import annotations

import argparse
import asyncio
import os
import time

from sonicwall import SonicWallClient
from sonicwall._exceptions import SonicWallError
from sonicwall.models.access_rule import AccessRule, AccessRuleAction, RuleAddress, RuleService
from sonicwall.models.nat_policy import NatPolicy
from sonicwall.models.service_object import PortRange, ServiceObject, ServiceProtocol


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _is_unsupported(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "api not found" in msg
        or "endpoint is incomplete" in msg
        or "command" in msg and "not found" in msg
    )


async def run(host: str, username: str, password: str) -> int:
    suffix = str(int(time.time()))
    failures = 0
    unsupported = 0
    async with SonicWallClient(host, username, password, verify_ssl=False) as client:
        # Service objects
        svc_name = f"sdk-svc-{suffix}"
        print("\n1) Service object write CRUD")
        try:
            svc = ServiceObject(name=svc_name, protocol=ServiceProtocol(tcp=PortRange(begin=65000, end=65000)))
            async with client.pending():
                await client.service_objects.create(svc)
                await client.service_objects.update(svc_name, ServiceObject(name=svc_name, protocol=ServiceProtocol(tcp=PortRange(begin=65001, end=65001))))
                await client.service_objects.delete(svc_name)
            _ok("service object create/update/delete succeeded")
        except SonicWallError as exc:
            if _is_unsupported(exc):
                _warn(f"service object CRUD unsupported on firmware: {exc}")
                unsupported += 1
            else:
                _fail(f"service object CRUD failed: {exc}")
                failures += 1

        # NAT policies
        nat_name = f"sdk-nat-{suffix}"
        print("\n2) NAT policy write CRUD")
        try:
            nat = NatPolicy(
                name=nat_name,
                inbound_interface="any",
                outbound_interface="X1",
                original_source="any",
                translated_source="original",
                original_destination="any",
                translated_destination="original",
                original_service="any",
                translated_service="original",
            )
            async with client.pending():
                await client.nat_policies.create(nat)
                await client.nat_policies.update(nat_name, nat)
                await client.nat_policies.delete(nat_name)
            _ok("NAT policy create/update/delete succeeded")
        except SonicWallError as exc:
            if _is_unsupported(exc):
                _warn(f"NAT policy CRUD unsupported on firmware: {exc}")
                unsupported += 1
            else:
                _fail(f"NAT policy CRUD failed: {exc}")
                failures += 1

        # Access rules
        rule_name = f"sdk-rule-{suffix}"
        print("\n3) Access rule write CRUD")
        try:
            rule = AccessRule(
                name=rule_name,
                **{"from": "LAN", "to": "WAN"},
                action=AccessRuleAction.DENY,
                source=RuleAddress(any=True),
                destination=RuleAddress(any=True),
                service=RuleService(any=True),
            )
            async with client.pending():
                await client.access_rules.create(rule)
                await client.access_rules.update("LAN", "WAN", rule_name, rule)
                await client.access_rules.delete("LAN", "WAN", rule_name)
            _ok("access rule create/update/delete succeeded")
        except SonicWallError as exc:
            if _is_unsupported(exc):
                _warn(f"access rule CRUD unsupported on firmware: {exc}")
                unsupported += 1
            else:
                _fail(f"access rule CRUD failed: {exc}")
                failures += 1

    print("\nSummary:")
    if failures:
        _fail(f"{failures} resource write CRUD area(s) failed")
    if unsupported:
        _warn(f"{unsupported} resource write CRUD area(s) unsupported on this firmware")
    if failures == 0:
        _ok("no hard failures detected")
    return 0 if failures == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate write CRUD on live SonicWall firmware")
    parser.add_argument("--host", default=os.getenv("SW_HOST", "192.168.0.1"))
    parser.add_argument("--user", default=os.getenv("SW_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("SW_PASS", ""))
    args = parser.parse_args()
    if not args.password:
        raise SystemExit("Error: provide --password or set SW_PASS env var")
    raise SystemExit(asyncio.run(run(args.host, args.user, args.password)))


if __name__ == "__main__":
    main()
