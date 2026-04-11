#!/usr/bin/env python3
"""Align packages/python, packages/typescript, and packages/go with repository root VERSION."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    raw = (root / "VERSION").read_text(encoding="utf-8").strip().splitlines()
    if not raw:
        raise SystemExit("VERSION is empty")
    ver = raw[0].strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?", ver):
        raise SystemExit(f"VERSION must be semver X.Y.Z (optional pre-release): {ver!r}")

    pp = root / "packages/python/pyproject.toml"
    text = pp.read_text(encoding="utf-8")
    pp.write_text(
        re.sub(r'^version = "[^"]+"', f'version = "{ver}"', text, count=1, flags=re.MULTILINE),
        encoding="utf-8",
    )

    pj = root / "packages/typescript/package.json"
    jt = pj.read_text(encoding="utf-8")
    pj.write_text(
        re.sub(
            r'^  "version": "[^"]+"',
            f'  "version": "{ver}"',
            jt,
            count=1,
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )

    vg = root / "packages/go/version.go"
    vg.write_text(
        "package sonicwall\n\n"
        "// Version is the SDK release version (aligned with Python and npm; see VERSION + CONTRIBUTING.md).\n"
        f'const Version = "{ver}"\n',
        encoding="utf-8",
    )
    print(ver)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
