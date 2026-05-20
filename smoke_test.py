#!/usr/bin/env python3
"""Smoke test against a live SonicWall device.

Usage:
    cd packages/python
    uv run ../../smoke_test.py --host 192.168.0.1 --user admin --password YOUR_PASSWORD

Or with env vars:
    SONICWALL_HOST=192.168.0.1 SONICWALL_USER=admin SONICWALL_PASS=secret uv run ../../smoke_test.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sonicwall._live_validation import resolve_live_credentials, run_smoke


def main() -> None:
    parser = argparse.ArgumentParser(description="SonicWall SDK smoke test")
    parser.add_argument("--host", default=None)
    parser.add_argument("--user", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    try:
        creds = resolve_live_credentials(
            host=args.host,
            username=args.user,
            password=args.password,
            require_password=True,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    sys.exit(asyncio.run(run_smoke(creds.host, creds.username, creds.password, verbose=True)))


if __name__ == "__main__":
    main()
