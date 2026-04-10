# TypeScript SDK — Getting Started

## Requirements

- Node.js 18+
- pnpm, npm, or yarn

## Installation

```bash
pnpm add @sonicwall/sdk
# or:
npm install @sonicwall/sdk
```

## Authentication behavior

The current TypeScript SDK implementation uses `Authorization: Basic ...` on
`POST /auth` and stores the returned `smngsess` session cookie for subsequent
requests.

On some SonicOS 7.x devices, auth may instead require Digest `auth-int` and
return a bearer token. If you are targeting those firmware variants, use the
Python SDK path as the reference implementation for now.

## Basic usage

```typescript
import { SonicWallClient } from "@sonicwall/sdk";

const client = new SonicWallClient({
  host: "192.168.1.1",
  username: "admin",
  password: "secret",
  verifySsl: false,   // default — disable for self-signed certs
  timeout: 30_000,
});

await client.connect();

try {
  // List address objects
  const objects = await client.addressObjects.list();
  console.log(`Found ${objects.length} address objects`);

  for (const obj of objects) {
    console.log(obj.name, obj.type, obj.host ?? obj.network);
  }
} finally {
  await client.disconnect();
}
```

## Transaction pattern

```typescript
// All writes inside the callback are committed atomically.
// On success: auto-commit. On error: auto-rollback.
await client.transaction(async () => {
  await client.addressObjects.create({
    name: "web-server",
    type: "host",
    host: "10.0.0.100",
    zone: "LAN",
  });

  await client.addressObjects.create({
    name: "db-server",
    type: "host",
    host: "10.0.0.200",
    zone: "LAN",
  });
  // Both created atomically — if db-server fails, web-server is rolled back
});
```

## Upsert

```typescript
const [obj, wasCreated] = await client.addressObjects.ensure({
  name: "web-server",
  type: "host",
  host: "10.0.0.100",
  zone: "LAN",
});
console.log(wasCreated ? "Created" : "Updated");
```

## Error handling

```typescript
import {
  NotFoundError,
  ConflictError,
  AuthenticationError,
  CommitError,
} from "@sonicwall/sdk";

try {
  const obj = await client.addressObjects.get("doesnt-exist");
} catch (err) {
  if (err instanceof NotFoundError) {
    console.log("Not found");
  } else if (err instanceof ConflictError) {
    console.log(`Already exists: ${err.sonicosMessage}`);
  } else if (err instanceof AuthenticationError) {
    console.log(`Auth failed: ${err.message}`);
  } else if (err instanceof CommitError) {
    console.log(`Commit failed: ${err.message}`);
  } else {
    throw err;
  }
}
```

## Type imports

```typescript
import type { AddressObject, AddressObjectType } from "@sonicwall/sdk";

const obj: AddressObject = {
  name: "test",
  type: "host" satisfies AddressObjectType,
  host: "10.0.0.1",
  zone: "LAN",
};
```

## ESM / CJS

The package ships both ESM and CJS builds. Import with `import` or `require`:

```typescript
// ESM (Node 18+, bundlers)
import { SonicWallClient } from "@sonicwall/sdk";

// CJS
const { SonicWallClient } = require("@sonicwall/sdk");
```