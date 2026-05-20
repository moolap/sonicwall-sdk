"""Live SonicWall device validation helpers (smoke + write CRUD).

Used by repo-root CLI scripts and pytest integration tests. Not part of the
public SDK API surface for library consumers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LiveCredentials:
    host: str
    username: str
    password: str


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def load_local_env() -> None:
    """Load ``.env`` from the repo root or current working directory if present.

    Requires the ``python-dotenv`` package (included in the ``dev`` extra).
    Existing shell environment variables take precedence over ``.env`` values.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    for directory in (Path.cwd(), *Path.cwd().parents):
        env_path = directory / ".env"
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            return

    load_dotenv(override=False)


def resolve_live_credentials(
    *,
    host: str | None = None,
    username: str | None = None,
    password: str | None = None,
    require_password: bool = True,
) -> LiveCredentials:
    """Resolve credentials from args and environment.

    Environment variables (first match wins per field):
    - Host: ``SONICWALL_HOST``, ``SW_HOST``
    - User: ``SONICWALL_USER``, ``SW_USER`` (default ``admin``)
    - Password: ``SONICWALL_PASS``, ``SONICWALL_PASSWORD``, ``SW_PASS``

  A gitignored ``.env`` at the repository root (see ``.env.example``) is loaded
  automatically when ``python-dotenv`` is installed.
    """
    load_local_env()
    resolved_host = host if host is not None else _env_first("SONICWALL_HOST", "SW_HOST", default="192.168.0.1")
    resolved_user = (
        username if username is not None else _env_first("SONICWALL_USER", "SW_USER", default="admin")
    )
    resolved_password = (
        password
        if password is not None
        else _env_first("SONICWALL_PASS", "SONICWALL_PASSWORD", "SW_PASS")
    )
    if require_password and not resolved_password:
        msg = (
            "Live device password required: pass --password, set SONICWALL_PASS "
            "(or SW_PASS), or add it to a .env file (see .env.example)"
        )
        raise ValueError(msg)
    return LiveCredentials(host=resolved_host, username=resolved_user, password=resolved_password)


def live_device_configured() -> bool:
    """True when host and password are available for integration tests."""
    try:
        resolve_live_credentials(require_password=True)
    except ValueError:
        return False
    return True


def integration_write_enabled() -> bool:
    """Destructive write CRUD tests require an explicit opt-in."""
    return os.getenv("SONICWALL_INTEGRATION_WRITE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


async def run_smoke(host: str, username: str, password: str, *, verbose: bool = False) -> int:
    """Run read-only + address-object write smoke checks. Returns error count."""
    from sonicwall import SonicWallClient
    from sonicwall._exceptions import NotFoundError, SonicWallError
    from sonicwall._firmware import is_firmware_unsupported_error
    from sonicwall.models.address_object import AddressObject, AddressObjectType

    def ok(msg: str) -> None:
        if verbose:
            print(f"  \033[32m✓\033[0m  {msg}")

    def fail(msg: str) -> None:
        if verbose:
            print(f"  \033[31m✗\033[0m  {msg}")

    def skip(msg: str) -> None:
        if verbose:
            print(f"  \033[33m-\033[0m  {msg}")

    def section(title: str) -> None:
        if verbose:
            print(f"\n\033[1m{title}\033[0m")

    errors = 0

    section("1. Authentication")
    try:
        client = SonicWallClient(host, username, password, verify_ssl=False)
        await client.connect()
        ok(f"Logged in to https://{host}")
    except SonicWallError as exc:
        fail(f"Login failed: {exc}")
        return 1

    async with client:
        section("2. Address objects (read-only)")
        try:
            objs = await client.address_objects.list()
            ok(f"Listed {len(objs)} address objects")
        except SonicWallError as exc:
            fail(f"address_objects.list() failed: {exc}")
            errors += 1

        section("3. Access rules (read-only)")
        try:
            rules = await client.access_rules.list()
            ok(f"Listed {len(rules)} access rules")
        except SonicWallError as exc:
            fail(f"access_rules.list() failed: {exc}")
            errors += 1

        section("4. Interfaces (read-only)")
        try:
            ifaces = await client.interfaces.list()
            ok(f"Listed {len(ifaces)} interfaces")
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                skip(f"interfaces.list() unsupported on this firmware: {exc}")
            else:
                fail(f"interfaces.list() failed: {exc}")
                errors += 1

        section("5. NAT policies (read-only)")
        try:
            nats = await client.nat_policies.list()
            ok(f"Listed {len(nats)} NAT policies")
        except SonicWallError as exc:
            fail(f"nat_policies.list() failed: {exc}")
            errors += 1

        section("6. Service objects (read-only)")
        try:
            svcs = await client.service_objects.list()
            ok(f"Listed {len(svcs)} service objects")
        except SonicWallError as exc:
            fail(f"service_objects.list() failed: {exc}")
            errors += 1

        section("7. DHCP leases (read-only)")
        try:
            leases = await client.dhcp.list_leases()
            ok(f"Listed {len(leases)} DHCP leases")
        except NotFoundError as exc:
            skip(f"dhcp.list_leases() unsupported on this firmware: {exc}")
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                skip(f"dhcp.list_leases() unsupported on this firmware: {exc}")
            else:
                fail(f"dhcp.list_leases() failed: {exc}")
                errors += 1

        section("8. Write test — create + delete a test address object")
        test_name = "sdk-smoke-test-DO-NOT-USE"
        try:
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
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                skip(f"write path requires config mode on this firmware: {exc}")
            else:
                fail(f"Write test failed: {exc}")
                errors += 1

    if verbose:
        section("Summary")
        if errors == 0:
            print("\n  \033[32mAll checks passed.\033[0m\n")
        else:
            print(f"\n  \033[31m{errors} check(s) failed.\033[0m\n")

    return errors


async def run_write_crud(host: str, username: str, password: str, *, verbose: bool = False) -> int:
    """Run destructive write CRUD checks. Returns 0 on success, 1 on hard failure."""
    import time

    from sonicwall import SonicWallClient
    from sonicwall._exceptions import SonicWallError
    from sonicwall._firmware import is_firmware_unsupported_error
    from sonicwall.models.access_rule import AccessRule, AccessRuleAction, RuleAddress, RuleService
    from sonicwall.models.nat_policy import NatPolicy
    from sonicwall.models.service_object import PortRange, ServiceObject, ServiceProtocol

    def ok(msg: str) -> None:
        if verbose:
            print(f"  [OK]  {msg}")

    def warn(msg: str) -> None:
        if verbose:
            print(f"  [WARN] {msg}")

    def fail(msg: str) -> None:
        if verbose:
            print(f"  [FAIL] {msg}")

    suffix = str(int(time.time()))
    failures = 0
    unsupported = 0
    async with SonicWallClient(host, username, password, verify_ssl=False) as client:
        svc_name = f"sdk-svc-{suffix}"
        if verbose:
            print("\n1) Service object write CRUD")
        try:
            svc = ServiceObject(
                name=svc_name,
                protocol=ServiceProtocol(tcp=PortRange(begin=65000, end=65000)),
            )
            async with client.pending():
                await client.service_objects.create(svc)
                await client.service_objects.update(
                    svc_name,
                    ServiceObject(
                        name=svc_name,
                        protocol=ServiceProtocol(tcp=PortRange(begin=65001, end=65001)),
                    ),
                )
                await client.service_objects.delete(svc_name)
            ok("service object create/update/delete succeeded")
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                warn(f"service object CRUD unsupported on firmware: {exc}")
                unsupported += 1
            else:
                fail(f"service object CRUD failed: {exc}")
                failures += 1

        nat_name = f"sdk-nat-{suffix}"
        if verbose:
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
            ok("NAT policy create/update/delete succeeded")
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                warn(f"NAT policy CRUD unsupported on firmware: {exc}")
                unsupported += 1
            else:
                fail(f"NAT policy CRUD failed: {exc}")
                failures += 1

        rule_name = f"sdk-rule-{suffix}"
        if verbose:
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
            ok("access rule create/update/delete succeeded")
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                warn(f"access rule CRUD unsupported on firmware: {exc}")
                unsupported += 1
            else:
                fail(f"access rule CRUD failed: {exc}")
                failures += 1

    if verbose:
        print("\nSummary:")
        if failures:
            fail(f"{failures} resource write CRUD area(s) failed")
        if unsupported:
            warn(f"{unsupported} resource write CRUD area(s) unsupported on this firmware")
        if failures == 0:
            ok("no hard failures detected")

    return 1 if failures else 0
