"""Shared response normalization helpers for firmware-variant envelopes."""

from __future__ import annotations

from typing import Any, Callable


def normalize_get_from_plural(
    response: dict[str, Any],
    *,
    plural_key: str,
    singular_key: str,
    predicate: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    """Normalize list-envelope get response into a singular envelope.

    Example:
      {"address_objects": [{"ipv4": {...}}]} -> {"address_object": {"ipv4": {...}}}
    """
    items = response.get(plural_key)
    if not isinstance(items, list) or not items:
        return response

    selected: dict[str, Any] | None = None
    if predicate is not None:
        for item in items:
            if isinstance(item, dict) and predicate(item):
                selected = item
                break
    if selected is None:
        first = items[0]
        if isinstance(first, dict):
            selected = first
    if selected is None:
        return response

    if singular_key in selected and isinstance(selected[singular_key], dict):
        return {singular_key: selected[singular_key]}
    return {singular_key: selected}


def unwrap_ipv4(item: dict[str, Any], wrapped_key: str) -> dict[str, Any] | None:
    """Return IPv4 payload from either wrapped or direct item."""
    if wrapped_key in item and isinstance(item[wrapped_key], dict):
        inner = item[wrapped_key]
        ipv4 = inner.get("ipv4")
        if isinstance(ipv4, dict):
            return ipv4
        return inner
    ipv4 = item.get("ipv4")
    if isinstance(ipv4, dict):
        return ipv4
    return None
