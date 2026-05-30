# Current Project Status

Last live validation: **2026-05-19** against `192.168.0.1` (Python SDK, Digest + bearer).

Commands run:

```bash
cd packages/python && uv run ../../smoke_test.py
SONICWALL_INTEGRATION_WRITE=1 uv run ../../validate_write_crud.py
```

## Live validation results (192.168.0.1)

| Check | Result | Notes |
|-------|--------|-------|
| Auth (Digest + bearer) | **Pass** | Login OK |
| Address objects list | **Pass** | 13 objects; 11 built-ins skipped (empty `host`/`network`) |
| Address object write (create/delete + commit) | **Pass** | `sdk-smoke-test-DO-NOT-USE` |
| Access rules list | **Pass** | 64 rules |
| NAT policies list | **Pass** | 8 policies |
| Service objects list | **Pass** | 205 objects |
| Interfaces list | **Skip** | HTTP 400: API endpoint is incomplete |
| DHCP leases list | **Skip** | HTTP 400: API endpoint is incomplete |
| Service object write CRUD | **Skip** | Create may succeed; follow-up command/API not found |
| NAT policy write CRUD | **Skip** | HTTP 404: API not found |
| Access rule write CRUD | **Skip** | HTTP 404: API not found |

**Conclusion:** This firmware profile is **production-ready for read automation and address-object writes**. Full write CRUD for rules/NAT/services is **not available via REST** on this device — treat those SDK methods as best-effort until SonicOS exposes the endpoints or a different firmware/model is validated.

## Completed in prior passes

- SonicOS 7.x Digest `auth-int` + bearer token auth (all four SDKs)
- Host normalization, contract capture (`collect_contract.py`)
- Firmware payload parsing fallbacks (address objects, NAT refs, service objects)
- Address-object schema-array write fallback
- Config-mode negotiation in pending transactions
- Transaction rollback robustness
- Endpoint support matrix + release readiness docs
- Multi-language CRUD parity (TS/Go/Java) for spec surface; Java + CI green on `dev`

## Next implementation tickets

1. ~~Live smoke on lab device~~ — done (see table above)
2. ~~Live write CRUD validation~~ — done; document unsupported writes (this file)
3. ~~Port Digest + bearer auth to TypeScript / Go / Java~~ — done
4. ~~Port Python firmware fallbacks + `UnsupportedEndpointError` to other languages~~ — done (schema-array fallbacks were already present; typed errors added)
5. Expand unit tests (Go suite, Java CRUD WireMock, access-rule/NAT/service Python tests)
6. First aligned OSS release (PyPI / npm / Go tag / Maven)
