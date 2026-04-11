#!/usr/bin/env python3
"""Bump patch version in Python, TypeScript, and Go package metadata (single source: pyproject.toml)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def bump_patch(v: str) -> str:
    base = v.split("-", 1)[0].split("+", 1)[0]
    parts = base.split(".")
    if len(parts) != 3:
        raise SystemExit(f"expected semver X.Y.Z (optional pre-release), got {v!r}")
    major, minor, patch = (int(parts[0]), int(parts[1]), int(parts[2]))
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    pp = root / "packages/python/pyproject.toml"
    text = pp.read_text(encoding="utf-8")
    m = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    if not m:
        raise SystemExit("no version = line in packages/python/pyproject.toml")
    cur = m.group(1)
    new = bump_patch(cur)
    pp.write_text(
        re.sub(r'^version = "[^"]+"', f'version = "{new}"', text, count=1, flags=re.MULTILINE),
        encoding="utf-8",
    )
    pj = root / "packages/typescript/package.json"
    jt = pj.read_text(encoding="utf-8")
    jt2 = re.sub(
        r'^  "version": "[^"]+"',
        f'  "version": "{new}"',
        jt,
        count=1,
        flags=re.MULTILINE,
    )
    pj.write_text(jt2, encoding="utf-8")
    vg = root / "packages/go/version.go"
    vg.write_text(
        'package sonicwall\n\n'
        '// Version is the SDK release version (aligned with Python and npm).\n'
        f'const Version = "{new}"\n',
        encoding="utf-8",
    )
    print(new)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
