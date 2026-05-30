#!/usr/bin/env python3
"""Run live validation with debug logs written to a file (for CI/agent runs)."""

from __future__ import annotations

import asyncio
import logging
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "live-validation.log"


def setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for h in list(root.handlers):
        root.removeHandler(h)
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(sh)


async def main() -> int:
    setup_logging()
    log = logging.getLogger("live_validation")
    log.info("=== Live validation started %s ===", datetime.now(UTC).isoformat())

    from sonicwall import SonicWallClient
    from sonicwall._exceptions import SonicWallError
    from sonicwall._firmware import is_firmware_unsupported_error
    from sonicwall._live_validation import load_local_env, resolve_live_credentials

    load_local_env()
    try:
        creds = resolve_live_credentials(require_password=True)
    except ValueError as exc:
        log.error("CONFIG: %s", exc)
        return 2

    log.info("Target host=%s user=%s", creds.host, creds.username)
    failures: list[str] = []
    skips: list[str] = []

    async def step(name: str, coro, timeout: float = 45.0) -> None:
        log.info("STEP begin: %s (timeout=%ss)", name, timeout)
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            detail = f"count={len(result)}" if hasattr(result, "__len__") else "ok"
            log.info("STEP pass: %s (%s)", name, detail)
        except TimeoutError:
            log.error("STEP timeout: %s after %ss", name, timeout)
            failures.append(f"{name}:timeout")
        except SonicWallError as exc:
            if is_firmware_unsupported_error(exc):
                log.warning("STEP skip: %s — %s", name, exc)
                skips.append(name)
            else:
                log.error("STEP fail: %s — %s", name, exc)
                failures.append(name)
        except Exception as exc:
            log.exception("STEP error: %s — %s", name, exc)
            failures.append(name)

    client = SonicWallClient(
        creds.host, creds.username, creds.password, verify_ssl=False, timeout=20.0
    )

    await step("auth.connect", client.connect(), timeout=60.0)

    if failures and failures[0] == "auth.connect":
        log.info("=== Summary: auth failed, stopping ===")
        log.info("Failures: %s", failures)
        log.info("Log file: %s", LOG_PATH)
        return 1

    async with client:
        await step("address_objects.list", client.address_objects.list())
        await step("access_rules.list", client.access_rules.list())
        await step("interfaces.list", client.interfaces.list())
        await step("nat_policies.list", client.nat_policies.list())
        await step("service_objects.list", client.service_objects.list())
        await step("dhcp.list_leases", client.dhcp.list_leases())

        from sonicwall.models.address_object import AddressObject, AddressObjectType

        test_name = "sdk-smoke-test-DO-NOT-USE"

        async def write_test() -> None:
            obj = AddressObject(
                name=test_name,
                type=AddressObjectType.HOST,
                zone="LAN",
                host="10.255.254.253",
            )
            async with client.pending():
                await client.address_objects.create(obj)
                await client.address_objects.delete(test_name)

        await step("address_object.write_delete", write_test(), timeout=90.0)

    log.info("=== Summary ===")
    log.info("Failures (%s): %s", len(failures), failures or "none")
    log.info("Skips (%s): %s", len(skips), skips or "none")
    log.info("Log file: %s", LOG_PATH)
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        code = asyncio.run(asyncio.wait_for(main(), timeout=180.0))
    except TimeoutError:
        logging.error("Overall validation timed out after 180s")
        code = 124
    except Exception:
        traceback.print_exc()
        code = 1
    print(f"EXIT_CODE={code}", flush=True)
    sys.exit(code)
