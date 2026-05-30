# Language parity matrix

Canonical API surface for **Python**, **TypeScript**, **Go**, and **Java**.  
**Python** is the reference for SonicOS 7.x auth (Digest + bearer) and firmware fallbacks.  
**TypeScript ≈ Go ≈ Java** target the same cookie-session CRUD surface below.

Legend: **Y** supported · **—** not applicable · **Py\*** Python-only today · **TS\*** TypeScript-only today

## Client lifecycle

| Capability | Python | TypeScript | Go | Java |
|------------|--------|------------|-----|------|
| Async client | `SonicWallClient` | `SonicWallClient` (async) | — (sync + `context`) | — (blocking) |
| Sync client | `SonicWallClientSync` | — | — | — |
| `connect` / `disconnect` | Y | Y | Y | Y |
| Context manager / auto-close | async + sync `with` | manual `disconnect` | manual | `AutoCloseable` |
| `commit` / `rollback` | Y | Y | Y | Y |
| `transaction` / `pending()` | `pending()` async · `transaction` all | `transaction` · nested depth **TS\*** | `Transaction` | `transaction` |
| TLS skip-verify option | Y | Y | Y | Y |

## Auth

| Capability | Python | TypeScript | Go | Java |
|------------|--------|------------|-----|------|
| SonicOS 7.x Digest + bearer | **Py\*** | — | — | — |
| Basic + `smngsess` cookie | fallback | Y | Y | Y |
| Session re-auth on expiry | Y | Y | Y | Y |
| `UnsupportedEndpointError` | **Py\*** | — | — | — |

## Resources

### Address objects (full CRUD + ensure)

| Op | Python | TS | Go | Java |
|----|--------|-----|-----|------|
| list / get / create / update / delete / ensure | Y | Y | Y | Y |

### Access rules

| Op | Python | TS | Go | Java |
|----|--------|-----|-----|------|
| list / get / create / update / delete | Y | Y | Y | Y |
| insertBefore / insertAfter | Y | Y | Y | Y |
| ensure | — | — | — | — |

### NAT policies

| Op | Python | TS | Go | Java |
|----|--------|-----|-----|------|
| list / get / create / update / delete / ensure | Y | Y | Y | Y |

### Service objects

| Op | Python | TS | Go | Java |
|----|--------|-----|-----|------|
| list / get / create / update / delete / ensure | Y | Y | Y | Y |

### Interfaces (read-only)

| Op | Python | TS | Go | Java |
|----|--------|-----|-----|------|
| list / get | Y | Y | Y | Y |

### DHCP leases (read-only)

| Op | Python | TS | Go | Java |
|----|--------|-----|-----|------|
| listLeases + firmware path fallbacks | Y | Y | Y | Y |

## Intentional differences (for now)

1. **Python auth** — only Python implements Digest `auth-int` + bearer for SonicOS 7.x lab devices.
2. **Nested `pending()`** — TypeScript tracks depth; others commit/rollback on outermost transaction only.
3. **`UnsupportedEndpointError`** — Python maps firmware “endpoint incomplete” messages; other SDKs surface generic HTTP errors until ported.
4. **Sync Python client** — mirrors async resources; use async client for `pending()` context manager.

## Verification

```bash
# Python
cd packages/python && uv run pytest tests/ -q

# TypeScript
cd packages/typescript && pnpm test

# Go
cd packages/go && go test ./...

# Java
cd packages/java && mvn test
```

When adding a resource operation, update this file and add tests in **all four** packages.
