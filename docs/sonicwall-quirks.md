# SonicOS REST API — Quirks and Gotchas

This document catalogs all known quirks in the SonicOS REST API that affect SDK design or usage.

---

## 1. Nested wire format (envelope wrapping)

Every object in the SonicOS REST API is wrapped in a typed envelope. A host address object on the wire looks like:

```json
{
  "address_object": {
    "ipv4": {
      "name": "my-server",
      "zone": "LAN",
      "host": { "ip": "10.0.0.100" }
    }
  }
}
```

List responses use a plural key containing an array of these envelopes:

```json
{
  "status": { "success": true, "info": [] },
  "address_objects": [
    { "address_object": { "ipv4": { ... } } },
    { "address_object": { "ipv4": { ... } } }
  ]
}
```

**Impact:** Every response must be unwrapped two levels before accessing object fields. The SDK handles this automatically.

---

## 2. Pending config — commit required

SonicOS does not persist changes immediately. All write operations (POST/PUT/DELETE on resource endpoints) stage changes into a "pending" queue visible to the current session. Changes must be explicitly committed:

```
POST /api/sonicos/config/pending   → commit all staged changes
DELETE /api/sonicos/config/pending → discard all staged changes
```

**Impact:**
- If your process crashes after writes but before commit, changes are lost.
- Uncommitted changes are visible to other admin sessions until committed or rolled back.
- Use the SDK's `pending()` context manager (Python) or `transaction()` (TS/Go) to ensure changes are always committed or rolled back.

---

## 3. Success=false on HTTP 200

SonicOS frequently returns HTTP 200 with `{"status": {"success": false, ...}}` to indicate errors such as "object not found" or "already exists". You cannot rely on the HTTP status code alone.

```json
{
  "status": {
    "success": false,
    "info": [{ "level": "error", "code": 1030, "message": "Object not found" }]
  }
}
```

**Notable SonicOS internal codes:**

| Code | Meaning |
|------|---------|
| 1030 | Object not found |
| 1055 | Object already exists (conflict) |
| 1085 | Session expired |

**Impact:** The SDK checks both the HTTP status code and the response body's `success` field on every response.

---

## 4. Session concurrency limit

SonicOS permits only a limited number of concurrent admin sessions (typically 3–5 depending on firmware). If the limit is exceeded, new authentication requests will fail with an error such as "Maximum number of admin sessions reached."

**Impact:**
- Do not create multiple SonicWallClient instances for the same device.
- Always call `disconnect()`/`Disconnect()` when done — this frees the session slot.
- If the process dies without logout, the session persists until it times out (default: 5 minutes).
- The SDK's context manager (`async with`/`with`) and `defer Disconnect()` pattern ensure cleanup.

---

## 5. Self-signed SSL certificates

All SonicWall management interfaces use HTTPS, but almost all deployments use the device's built-in self-signed certificate. This causes TLS verification to fail with standard settings.

**SDK default:** `verify_ssl=False` / `WithTLSSkipVerify(true)` — TLS verification is disabled by default.

**Production recommendation:** Replace the self-signed cert with one signed by an internal CA and enable verification:

```python
client = SonicWallClient(host, user, pass, verify_ssl=True)
```

---

## 6. Access rule ordering — first match wins

SonicOS evaluates access rules top-down; the first matching rule determines the action. Rule ordering matters significantly. The REST API does not offer a simple "insert at position N" operation.

Rules have a `priority` field:
- `{"priority": {"auto": true}}` — SonicOS assigns a priority automatically (appends to the zone-pair list).
- `{"priority": {"value": N}}` — explicit numeric priority. Lower numbers are evaluated first.

**Impact:**
- When creating rules that must evaluate before existing rules, use explicit priority values.
- The SDK provides `insert_before()` / `insert_after()` (Python) to help with ordering, but these work by reading the target rule's priority — if auto-priority is in use, ordering is not guaranteed.
- Always verify rule ordering after creation on critical deployments.

---

## 7. Zone-scoped name uniqueness

Address object names must be unique within a zone, not globally. The same name can appear in multiple zones. The REST API includes the zone in the object body, and the get-by-name endpoint (`/name/{name}`) returns the first match — which may not be the one you expect if names are duplicated across zones.

**Impact:** Use distinct names across all zones to avoid ambiguity. The SDK `get(name)` endpoint calls `/name/{name}` directly and returns the first match SonicOS provides.

---

## 8. Access rule get path includes zone pair

Access rules are fetched by zone pair + name, not by name alone:

```
GET /api/sonicos/access-rules/ipv4/from/{from_zone}/to/{to_zone}/name/{name}
```

**Impact:** You must know the from/to zones to fetch or update a rule. The `list()` call returns all rules including their zones, so you can discover the full key from the list response.

---

## 9. Subnet mask format (dotted decimal, not CIDR)

The SonicOS API represents network objects using a separate subnet address and dotted-decimal mask, not CIDR notation:

```json
{
  "network": {
    "subnet": "10.0.0.0",
    "mask": "255.255.255.0"
  }
}
```

**Impact:** The SDK converts between CIDR (`10.0.0.0/24`) and the SonicOS dotted-decimal format automatically in both directions.

---

## 10. Range endpoints use "begin"/"end", not "start"/"end"

SonicOS uses `begin` and `end` for IP range boundaries in the wire format. This is inconsistent with many other APIs that use `start`/`end`.

```json
{ "range": { "begin": "10.0.0.10", "end": "10.0.0.20" } }
```

**Impact:** The Python SDK aliases these as `range_start`/`range_end` in the model but serialises as `begin`/`end` on the wire.

---

## 11. POST does not return the created object

When creating a resource (POST), SonicOS returns only a status response, not the newly created object body:

```json
{ "status": { "success": true, "info": [{"code": 200, "message": "OK"}] } }
```

**Impact:** After a successful POST, the SDK performs a subsequent GET to retrieve the canonical object representation. This means creates require two API calls.

---

## 12. SonicOS 7 authentication requires Digest `auth-int` handshake

On SonicOS 7.x devices, authentication is a two-step Digest flow (with
`qop=auth-int`), not a single Basic-auth request:

1. `POST /api/sonicos/auth` with `{}` and no auth header returns `401` with
   `WWW-Authenticate: Digest ... qop="auth-int"`.
2. Client computes and sends `Authorization: Digest ...` with body integrity
   (`auth-int`) for the same `{}` body.
3. Successful response returns status info containing a `bearer_token`.

```
POST /api/sonicos/auth
Content-Type: application/json

{}
-> 401 WWW-Authenticate: Digest ... qop="auth-int"
```

---

## 13. Auth token format differs by firmware

SonicOS 7.x commonly returns a `bearer_token` in the auth response body, and
subsequent requests use:

```
Authorization: Bearer <token>
```

Some older firmware variants use the `smngsess` cookie instead:

```
Cookie: smngsess=<value>
```

**Impact:** SDK implementations may differ by language/version while targeting
the same API family. The current Python SDK uses Digest `auth-int` + Bearer
token for SonicOS 7.x.