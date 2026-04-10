# Endpoint Support Matrix

This matrix shows:

- **Spec support:** what this repo's partial OpenAPI spec declares (`spec/openapi.yaml`)
- **SDK support:** what the Python SDK currently implements
- **Firmware support (validated device):** what was observed on the tested SonicOS device during smoke + contract runs

## Legend

- `Supported` = works on validated firmware
- `Supported with quirks` = works with compatibility fallbacks in SDK
- `Unsupported on validated firmware` = endpoint exists in spec/SDK but firmware returns not found/incomplete
- `Not in current SDK scope` = outside this repo's implemented resource set

## Core Auth and Transaction

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `POST /auth` | Yes | Yes | Supported with quirks | Digest `auth-int` + bearer token flow works |
| `DELETE /auth` | Yes | Yes | Supported | Logout works |
| `POST /config/pending` | Yes | Yes | Supported | Commit works |
| `DELETE /config/pending` | Yes | Yes | Supported with quirks | May return `Non config mode` depending on transaction state |
| Config mode endpoints (`/config/mode`, etc.) | No | Yes (best-effort probes) | Supported with quirks | Added for firmware that requires explicit config mode for writes |

## Address Objects

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `GET /address-objects/ipv4` | Yes | Yes | Supported with quirks | Some built-in entries are malformed (`host: {}`, `network: {}`) and skipped |
| `GET /address-objects/ipv4/name/{name}` | Yes | Yes | Supported with quirks | Firmware can return list envelope (`address_objects`) instead of single object |
| `POST /address-objects/ipv4` | Yes | Yes | Supported with quirks | Some firmware expects `address_objects: [ ... ]`; SDK auto-retries alternate payload |
| `PUT /address-objects/ipv4/name/{name}` | Yes | Yes | Supported with quirks | Same payload fallback as POST |
| `DELETE /address-objects/ipv4/name/{name}` | Yes | Yes | Supported | Delete works in validated smoke write test |

## Access Rules

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `GET /access-rules/ipv4` | Yes | Yes | Supported | List works |
| `GET /access-rules/ipv4/from/{from}/to/{to}/name/{name}` | Yes | Yes | Unsupported on validated firmware | Device returned `API not found` in contract probe |
| `POST /access-rules/ipv4` | Yes | Yes | Not yet validated on device | Not exercised in smoke write path |
| `PUT /access-rules/ipv4/from/{from}/to/{to}/name/{name}` | Yes | Yes | Not yet validated on device | Not exercised |
| `DELETE /access-rules/ipv4/from/{from}/to/{to}/name/{name}` | Yes | Yes | Not yet validated on device | Not exercised |

## Interfaces

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `GET /interfaces` | Yes | Yes | Unsupported on validated firmware | Returned `400 API endpoint is incomplete` |
| `GET /interfaces/name/{name}` | Yes | Yes | Not yet validated on device | Not reachable due to list endpoint limitation |

## NAT Policies

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `GET /nat-policies/ipv4` | Yes | Yes | Supported with quirks | Parser handles firmware shape (`inbound`, `outbound`, object refs) |
| `GET /nat-policies/ipv4/name/{name}` | Yes | Yes | Unsupported on validated firmware | Returned `API not found` in contract probe |
| `POST /nat-policies/ipv4` | Yes | Yes | Not yet validated on device | Not exercised in smoke write path |
| `PUT /nat-policies/ipv4/name/{name}` | Yes | Yes | Not yet validated on device | Not exercised |
| `DELETE /nat-policies/ipv4/name/{name}` | Yes | Yes | Not yet validated on device | Not exercised |

## Service Objects

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `GET /service-objects` | Yes | Yes | Supported with quirks | Built-in names can exceed 31 chars; parser accepts them |
| `GET /service-objects/name/{name}` | Yes | Yes | Supported with quirks | Firmware returns list envelope; parser tolerates current shape |
| `POST /service-objects` | Yes | Yes | Not yet validated on device | Not exercised in smoke write path |
| `PUT /service-objects/name/{name}` | Yes | Yes | Not yet validated on device | Not exercised |
| `DELETE /service-objects/name/{name}` | Yes | Yes | Not yet validated on device | Not exercised |

## DHCP

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `GET /dhcp/server/lease` | Yes | Yes | Unsupported on validated firmware | Returned `404 API not found` or `400 API endpoint is incomplete` depending on run |
| Fallback variants (`/dhcp/server/leases`, `/dhcp/leases`, `/dhcp-server/lease`) | No | Yes | Not found/incomplete on validated firmware | SDK probes these variants automatically |

## Scope Boundary

This matrix covers the resources implemented in this SDK repo. It does **not**
claim full SonicOS API coverage outside these endpoints.
