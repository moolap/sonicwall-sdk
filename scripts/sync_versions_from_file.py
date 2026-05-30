#!/usr/bin/env python3
"""Align packages/python, packages/typescript, packages/go, and packages/java with repository root VERSION."""
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

    pj_java = root / "packages/java/pom.xml"
    jt_java = pj_java.read_text(encoding="utf-8")
    pj_java.write_text(
        re.sub(
            r"(<artifactId>sonicwall-sdk</artifactId>\s*\n\s*<version>)[^<]+(</version>)",
            rf"\g<1>{ver}\2",
            jt_java,
            count=1,
        ),
        encoding="utf-8",
    )

    vj = root / "packages/java/src/main/java/tech/gandiva/sonicwall/Version.java"
    vj.write_text(
        "package tech.gandiva.sonicwall;\n\n"
        "/** SDK release version (aligned with Python, TypeScript, Go; see repository {@code VERSION}). */\n"
        "public final class Version {\n"
        f'  public static final String VERSION = "{ver}";\n\n'
        "  private Version() {}\n"
        "}\n",
        encoding="utf-8",
    )
    print(ver)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
