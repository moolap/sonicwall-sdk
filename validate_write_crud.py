#!/usr/bin/env python3
"""Live firmware write CRUD validator for key resources."""

from __future__ import annotations

import argparse
import asyncio
import sys

from sonicwall._live_validation import resolve_live_credentials, run_write_crud


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate write CRUD on live SonicWall firmware")
    parser.add_argument("--host", default=None)
    parser.add_argument("--user", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-step output (for scripting)",
    )
    args = parser.parse_args()

    try:
        creds = resolve_live_credentials(
            host=args.host,
            username=args.user,
            password=args.password,
            require_password=True,
        )
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    exit_code = asyncio.run(
        run_write_crud(
            creds.host,
            creds.username,
            creds.password,
            verbose=not args.quiet,
        )
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
