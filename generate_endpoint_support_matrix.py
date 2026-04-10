#!/usr/bin/env python3
"""Generate docs/endpoint-support-matrix.md from spec + status JSON."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "spec" / "openapi.yaml"
STATUS = ROOT / "docs" / "endpoint-support-status.json"
OUT = ROOT / "docs" / "endpoint-support-matrix.md"


def parse_spec_endpoints(spec_text: str) -> list[tuple[str, str]]:
    in_paths = False
    current_path: str | None = None
    endpoints: list[tuple[str, str]] = []
    methods = {"get", "post", "put", "delete", "patch"}

    for raw in spec_text.splitlines():
        line = raw.rstrip()
        if line.startswith("paths:"):
            in_paths = True
            continue
        if not in_paths:
            continue
        if line and not line.startswith(" "):
            break

        if line.startswith("  /") and line.endswith(":"):
            current_path = line.strip()[:-1]
            continue
        if current_path and line.startswith("    "):
            token = line.strip().rstrip(":").lower()
            if token in methods:
                endpoints.append((token.upper(), current_path))

    return endpoints


def render() -> str:
    endpoints = parse_spec_endpoints(SPEC.read_text(encoding="utf-8"))
    statuses = json.loads(STATUS.read_text(encoding="utf-8"))
    lines = [
        "# Endpoint Support Matrix",
        "",
        "Auto-generated from `spec/openapi.yaml` and `docs/endpoint-support-status.json`.",
        "",
        "| Endpoint | Spec | Python SDK | Validated firmware status | Notes |",
        "|---|---|---|---|---|",
    ]
    for method, path in endpoints:
        key = f"{method} {path}"
        st = statuses.get(key, {})
        sdk_status = st.get("sdk_status", "unknown")
        fw_status = st.get("firmware_status", "not_yet_validated")
        notes = st.get("notes", "")
        lines.append(f"| `{key}` | Yes | {sdk_status} | {fw_status} | {notes} |")
    lines.append("")
    lines.append("Legend:")
    lines.append("- `supported`")
    lines.append("- `supported_with_fallback`")
    lines.append("- `supported_with_quirks`")
    lines.append("- `unsupported_on_validated_firmware`")
    lines.append("- `not_yet_validated`")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.write_text(render(), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
