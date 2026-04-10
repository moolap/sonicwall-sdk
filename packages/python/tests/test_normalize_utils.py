"""Tests for shared response normalization helpers."""

from __future__ import annotations

from sonicwall.resources._normalize import normalize_get_from_plural, unwrap_ipv4


def test_normalize_get_from_plural_uses_predicate_match() -> None:
    response = {
        "address_objects": [
            {"ipv4": {"name": "a", "host": {"ip": "1.1.1.1"}}},
            {"ipv4": {"name": "b", "host": {"ip": "2.2.2.2"}}},
        ]
    }
    out = normalize_get_from_plural(
        response,
        plural_key="address_objects",
        singular_key="address_object",
        predicate=lambda item: (unwrap_ipv4(item, "address_object") or {}).get("name") == "b",
    )
    assert out["address_object"]["ipv4"]["name"] == "b"


def test_unwrap_ipv4_handles_wrapped_and_direct() -> None:
    assert unwrap_ipv4({"address_object": {"ipv4": {"name": "x"}}}, "address_object") == {"name": "x"}
    assert unwrap_ipv4({"ipv4": {"name": "y"}}, "address_object") == {"name": "y"}
