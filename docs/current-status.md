# Current Project Status

This document captures what was completed in the recent SonicOS firmware
compatibility pass and what remains for the next implementation cycle.

## Completed in this pass

- Implemented Python auth flow for SonicOS 7.x Digest `auth-int` handshake
  and bearer-token usage.
- Added host normalization so client accepts either host/IP or full URL input.
- Added one-shot contract capture tool: `collect_contract.py`.
- Hardened parsing against real firmware payload variants:
  - address objects (`host`/`network` malformed or alternate shapes)
  - NAT policy reference/object variants
  - service object long built-in names
  - address-object get-by-name list-envelope variants
- Added write compatibility fallback for address object payload schema
  (`address_object` vs `address_objects[]`).
- Added config-mode negotiation attempts in pending transaction context
  for firmware requiring explicit mode transition before writes.
- Improved transaction robustness so rollback failures do not mask the original
  write exception.
- Expanded smoke test behavior for firmware-limited endpoints (skip unsupported
  interfaces/DHCP/write mode constraints instead of hard fail where appropriate).
- Added and updated tests for all compatibility fixes.
- Added endpoint support documentation:
  - `docs/endpoint-support-matrix.md`
  - `docs/release-readiness.md`

## Validated on target firmware/device

- Supported: auth, address object list/get/create/delete flow, access-rule list,
  NAT list, service-object list, transaction commit path.
- Supported with quirks: address object parsing (malformed built-ins skipped).
- Unsupported on validated firmware: interfaces list endpoint, DHCP lease
  endpoint variants.

## Identified next implementation tickets

- Live-validate write CRUD for access rules.
- Live-validate write CRUD for NAT policies.
- Live-validate write CRUD for service objects.
- Build shared response normalization utilities across resources.
- Auto-generate endpoint support matrix from contract captures.
- Port critical Python compatibility fallbacks to TypeScript and Go SDKs.
