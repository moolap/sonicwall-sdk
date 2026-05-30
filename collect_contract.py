#!/usr/bin/env python3
"""Collect raw SonicOS API request/response contracts in one pass.

Usage:
  cd packages/python
  uv run ../../collect_contract.py --host 192.168.0.1 --user admin --password '...'

Output:
  JSON report written to ./contract-captures/contract-<timestamp>.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from sonicwall import SonicWallClient
from sonicwall._live_validation import resolve_live_credentials


@dataclass
class ProbeResult:
    name: str
    method: str
    path: str
    request_body: dict[str, Any] | None
    status_code: int
    response_json: dict[str, Any] | list[Any] | None
    response_text: str | None
    error: str | None = None


def _now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _safe_json(resp: httpx.Response) -> dict[str, Any] | list[Any] | None:
    try:
        return resp.json()
    except Exception:
        return None


async def _raw_request(
    client: SonicWallClient,
    *,
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
    name: str,
) -> ProbeResult:
    url = f"{client._http._base_url}/{path.lstrip('/')}"  # noqa: SLF001
    headers: dict[str, str] = {"Accept": "application/json"}
    headers.update(client._auth._auth_headers())  # noqa: SLF001
    if json_body is not None:
        headers["Content-Type"] = "application/json"

    try:
        resp = await client._http._client.request(  # noqa: SLF001
            method=method,
            url=url,
            json=json_body,
            headers=headers,
        )
        parsed = _safe_json(resp)
        text = None if parsed is not None else resp.text
        return ProbeResult(
            name=name,
            method=method,
            path=path,
            request_body=json_body,
            status_code=resp.status_code,
            response_json=parsed,
            response_text=text,
        )
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(
            name=name,
            method=method,
            path=path,
            request_body=json_body,
            status_code=0,
            response_json=None,
            response_text=None,
            error=str(exc),
        )


def _extract_first_name(payload: Any, list_key: str, item_key: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    items = payload.get(list_key, [])
    if not isinstance(items, list) or not items:
        return None
    first = items[0]
    if not isinstance(first, dict):
        return None
    wrapped = first.get(item_key, first)
    if isinstance(wrapped, dict) and "ipv4" in wrapped and isinstance(wrapped["ipv4"], dict):
        wrapped = wrapped["ipv4"]
    if not isinstance(wrapped, dict):
        return None
    name = wrapped.get("name")
    return name if isinstance(name, str) and name else None


def _extract_first_access_rule(payload: Any) -> tuple[str, str, str] | None:
    if not isinstance(payload, dict):
        return None
    items = payload.get("access_rules", [])
    if not isinstance(items, list) or not items:
        return None
    first = items[0]
    if not isinstance(first, dict):
        return None
    body = first.get("access_rule", first)
    if isinstance(body, dict) and "ipv4" in body and isinstance(body["ipv4"], dict):
        body = body["ipv4"]
    if not isinstance(body, dict):
        return None
    from_zone = body.get("from")
    to_zone = body.get("to")
    name = body.get("name")
    if all(isinstance(v, str) and v for v in (from_zone, to_zone, name)):
        return from_zone, to_zone, name
    return None


async def run(host: str, username: str, password: str, output_dir: str) -> int:
    client = SonicWallClient(host, username, password, verify_ssl=False)
    results: list[ProbeResult] = []

    await client.connect()
    try:
        # Read/list endpoints
        for method, path, name in [
            ("GET", "/address-objects/ipv4", "address_objects.list"),
            ("GET", "/access-rules/ipv4", "access_rules.list"),
            ("GET", "/interfaces", "interfaces.list"),
            ("GET", "/nat-policies/ipv4", "nat_policies.list"),
            ("GET", "/service-objects", "service_objects.list"),
            ("GET", "/dhcp/server/lease", "dhcp.list_leases"),
        ]:
            results.append(await _raw_request(client, method=method, path=path, name=name))

        # Follow-up gets based on list responses
        addr_list = next((r for r in results if r.name == "address_objects.list"), None)
        if addr_list:
            addr_name = _extract_first_name(addr_list.response_json, "address_objects", "address_object")
            if addr_name:
                results.append(
                    await _raw_request(
                        client,
                        method="GET",
                        path=f"/address-objects/ipv4/name/{addr_name}",
                        name="address_objects.get(first)",
                    )
                )

        svc_list = next((r for r in results if r.name == "service_objects.list"), None)
        if svc_list:
            svc_name = _extract_first_name(svc_list.response_json, "service_objects", "service_object")
            if svc_name:
                results.append(
                    await _raw_request(
                        client,
                        method="GET",
                        path=f"/service-objects/name/{svc_name}",
                        name="service_objects.get(first)",
                    )
                )

        nat_list = next((r for r in results if r.name == "nat_policies.list"), None)
        if nat_list:
            nat_name = _extract_first_name(nat_list.response_json, "nat_policies", "nat_policy")
            if nat_name:
                results.append(
                    await _raw_request(
                        client,
                        method="GET",
                        path=f"/nat-policies/ipv4/name/{nat_name}",
                        name="nat_policies.get(first)",
                    )
                )

        iface_list = next((r for r in results if r.name == "interfaces.list"), None)
        if iface_list:
            iface_name = _extract_first_name(iface_list.response_json, "interfaces", "interface")
            if iface_name:
                results.append(
                    await _raw_request(
                        client,
                        method="GET",
                        path=f"/interfaces/name/{iface_name}",
                        name="interfaces.get(first)",
                    )
                )

        rule_list = next((r for r in results if r.name == "access_rules.list"), None)
        if rule_list:
            key = _extract_first_access_rule(rule_list.response_json)
            if key:
                from_zone, to_zone, name = key
                results.append(
                    await _raw_request(
                        client,
                        method="GET",
                        path=f"/access-rules/ipv4/from/{from_zone}/to/{to_zone}/name/{name}",
                        name="access_rules.get(first)",
                    )
                )
    finally:
        await client.disconnect()

    output = {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "host": host,
        "result_count": len(results),
        "results": [r.__dict__ for r in results],
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"contract-{_now_stamp()}.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote contract capture: {out_path}")

    errors = [r for r in results if r.error]
    print(f"Captured {len(results)} endpoint interactions; errors={len(errors)}")
    return 0 if not errors else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect SonicOS API contracts")
    parser.add_argument("--host", default=None)
    parser.add_argument("--user", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--output-dir", default="contract-captures")
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

    raise SystemExit(asyncio.run(run(creds.host, creds.username, creds.password, args.output_dir)))


if __name__ == "__main__":
    main()
