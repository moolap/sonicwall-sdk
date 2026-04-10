# Endpoint Support Matrix

Auto-generated from `spec/openapi.yaml` and `docs/endpoint-support-status.json`.

| Endpoint | Spec | Python SDK | Validated firmware status | Notes |
|---|---|---|---|---|
| `POST /auth` | Yes | supported | supported_with_quirks | Digest auth-int + bearer token flow validated. |
| `DELETE /auth` | Yes | supported | supported | Logout works. |
| `POST /config/pending` | Yes | supported | supported | Commit works. |
| `DELETE /config/pending` | Yes | supported | supported_with_quirks | Can return Non config mode depending on transaction state. |
| `GET /address-objects/ipv4` | Yes | supported | supported_with_quirks | Malformed built-ins are skipped. |
| `POST /address-objects/ipv4` | Yes | supported | supported_with_quirks | SDK retries firmware schema variant payload. |
| `GET /address-objects/ipv4/name/{name}` | Yes | supported | supported_with_quirks | Firmware may return list envelope; SDK normalizes. |
| `PUT /address-objects/ipv4/name/{name}` | Yes | supported | supported_with_quirks | SDK retries firmware schema variant payload. |
| `DELETE /address-objects/ipv4/name/{name}` | Yes | supported | supported | Validated in smoke write flow. |
| `GET /access-rules/ipv4` | Yes | supported | supported | List works. |
| `POST /access-rules/ipv4` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates API not found on validated firmware profile. |
| `GET /access-rules/ipv4/from/{from_zone}/to/{to_zone}/name/{name}` | Yes | supported_with_fallback | supported_with_quirks | Direct endpoint can 404; SDK falls back to list matching. |
| `PUT /access-rules/ipv4/from/{from_zone}/to/{to_zone}/name/{name}` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates API not found on validated firmware profile. |
| `DELETE /access-rules/ipv4/from/{from_zone}/to/{to_zone}/name/{name}` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates API not found on validated firmware profile. |
| `GET /interfaces` | Yes | supported | unsupported_on_validated_firmware | Endpoint returns API endpoint is incomplete. |
| `GET /interfaces/name/{name}` | Yes | supported | not_yet_validated | Not reachable on validated firmware due to list endpoint behavior. |
| `GET /nat-policies/ipv4` | Yes | supported_with_fallback | supported_with_quirks | Parser handles inbound/outbound and object-ref variants. |
| `POST /nat-policies/ipv4` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates API not found on validated firmware profile. |
| `GET /nat-policies/ipv4/name/{name}` | Yes | supported_with_fallback | supported_with_quirks | Direct endpoint can 404; SDK falls back to list matching. |
| `PUT /nat-policies/ipv4/name/{name}` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates API not found on validated firmware profile. |
| `DELETE /nat-policies/ipv4/name/{name}` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates API not found on validated firmware profile. |
| `GET /service-objects` | Yes | supported_with_fallback | supported_with_quirks | Long built-in names and envelope variants supported. |
| `POST /service-objects` | Yes | supported | unsupported_on_validated_firmware | Create may succeed but follow-up command path is not found on validated firmware. |
| `GET /service-objects/name/{name}` | Yes | supported_with_fallback | supported_with_quirks | Direct endpoint can return list envelope; SDK normalizes/falls back. |
| `PUT /service-objects/name/{name}` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates command/API not found on validated firmware profile. |
| `DELETE /service-objects/name/{name}` | Yes | supported | unsupported_on_validated_firmware | Write validation indicates command/API not found on validated firmware profile. |
| `GET /dhcp/server/lease` | Yes | supported_with_fallback | unsupported_on_validated_firmware | Primary and fallback DHCP endpoints are unavailable/incomplete on validated firmware. |

Legend:
- `supported`
- `supported_with_fallback`
- `supported_with_quirks`
- `unsupported_on_validated_firmware`
- `not_yet_validated`
