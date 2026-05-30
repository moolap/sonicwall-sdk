# SonicWall SDK

[![PyPI](https://img.shields.io/pypi/v/sonicwall-sdk?label=PyPI)](https://pypi.org/project/sonicwall-sdk/)
[![npm](https://img.shields.io/npm/v/@sonicwall/sdk?label=npm)](https://www.npmjs.com/package/@sonicwall/sdk)
[![Go Reference](https://pkg.go.dev/badge/github.com/gandiva-tech/sonicwall-sdk/go.svg)](https://pkg.go.dev/github.com/gandiva-tech/sonicwall-sdk/go)
[![GitLab CI](https://gitlab.com/gandiva-tech/sonicwall-sdk/badges/main/pipeline.svg)](https://gitlab.com/gandiva-tech/sonicwall-sdk/-/pipelines)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Multi-language SDK for the SonicOS REST API. Manage address objects, access rules, NAT policies, interfaces, service objects, and DHCP from Python, TypeScript, Go, or Java — with proper session management, pending-config transactions, and typed errors.

## Features

- Session-based auth with automatic re-authentication on expiry
- Pending-config transaction context manager / helper
- Full CRUD for: address objects, access rules, NAT policies, service objects, DHCP
- Read-only interface listing
- Self-signed certificate support (default: SSL verification disabled)
- Async-first Python with sync wrapper; async TypeScript; idiomatic Go

## Authentication Matrix

| SDK | Current auth implementation | Firmware notes |
|---|---|---|
| Python | Digest `auth-int` handshake on `POST /auth`, then `Authorization: Bearer <token>` | Targets SonicOS 7.x behavior where auth returns `bearer_token` |
| TypeScript | `Authorization: Basic ...` on `POST /auth`, then `Cookie: smngsess=...` | Works for cookie-based firmware variants |
| Go | `Authorization: Basic ...` on `POST /auth`, then `Cookie: smngsess=...` | Works for cookie-based firmware variants |
| Java | `Authorization: Basic ...` on `POST /auth`, then `Cookie: smngsess=...` | Works for cookie-based firmware variants |

If your target device requires Digest `auth-int` + bearer token, use Python now
or plan parity updates for TypeScript/Go before production rollout.

## Installation

### Python

```bash
pip install sonicwall-sdk
# or with uv:
uv add sonicwall-sdk
```

### TypeScript / Node.js

```bash
pnpm add @sonicwall/sdk
# or:
npm install @sonicwall/sdk
```

### Go

```bash
go get github.com/gandiva-tech/sonicwall-sdk/go
```

### Java

```bash
cd packages/java && mvn install
```

Maven dependency:

```xml
<dependency>
  <groupId>tech.gandiva</groupId>
  <artifactId>sonicwall-sdk</artifactId>
  <version>0.1.0</version>
</dependency>
```

## Quick Start

### Python (async)

```python
import asyncio
from sonicwall import SonicWallClient
from sonicwall.models import AddressObject, AddressObjectType

async def main():
    async with SonicWallClient("192.168.1.1", "admin", "password") as client:
        # List all IPv4 address objects
        objects = await client.address_objects.list()
        for obj in objects:
            print(obj.name, obj.type, obj.host)

        # Create an address object inside a pending-config transaction
        async with client.pending():
            new_obj = AddressObject(
                name="my-server",
                type=AddressObjectType.HOST,
                host="10.0.0.100",
                zone="LAN",
            )
            created, was_new = await client.address_objects.ensure(new_obj)
            print(f"{'Created' if was_new else 'Updated'}: {created.name}")
        # pending() commits on clean exit, rolls back on exception

asyncio.run(main())
```

### Python (sync)

```python
from sonicwall import SonicWallClientSync
from sonicwall.models import AddressObject, AddressObjectType

with SonicWallClientSync("192.168.1.1", "admin", "password") as client:
    objs = client.address_objects.list()
    print(f"Found {len(objs)} address objects")

    obj = client.address_objects.get("my-server")
    print(obj.host)
```

### TypeScript

```typescript
import { SonicWallClient } from "@sonicwall/sdk";

const client = new SonicWallClient({
  host: "192.168.1.1",
  username: "admin",
  password: "password",
});

await client.connect();

try {
  const objects = await client.addressObjects.list();
  console.log(`Found ${objects.length} address objects`);

  // Create within a transaction
  await client.transaction(async () => {
    await client.addressObjects.create({
      name: "my-server",
      type: "host",
      host: "10.0.0.100",
      zone: "LAN",
    });
  }); // auto-commits or rolls back
} finally {
  await client.disconnect();
}
```

### Go

```go
package main

import (
    "context"
    "fmt"
    "log"

    sonicwall "github.com/gandiva-tech/sonicwall-sdk/go"
)

func main() {
    client, err := sonicwall.NewClient("192.168.1.1", "admin", "password",
        sonicwall.WithTLSSkipVerify(true),
    )
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()
    if err := client.Connect(ctx); err != nil {
        log.Fatal(err)
    }
    defer client.Disconnect(ctx)

    objects, err := client.AddressObjects.List(ctx)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Found %d address objects\n", len(objects))

    // Transactional create
    err = client.Transaction(ctx, func(ctx context.Context) error {
        _, _, err := client.AddressObjects.Ensure(ctx, &sonicwall.AddressObjectIPv4{
            Name: "my-server",
            Type: sonicwall.AddressObjectTypeHost,
            Host: "10.0.0.100",
            Zone: "LAN",
        })
        return err
    })
    if err != nil {
        log.Fatal(err)
    }
}
```

## Error Handling

```python
from sonicwall import NotFoundError, ConflictError, AuthenticationError, UnsupportedEndpointError

try:
    obj = await client.address_objects.get("nonexistent")
except NotFoundError:
    print("Object not found")
except ConflictError as e:
    print(f"Already exists: {e}")
except AuthenticationError:
    print("Bad credentials")
```

## Documentation

- [Python guide](docs/python.md)
- [TypeScript guide](docs/typescript.md)
- [Go guide](docs/go.md)
- [Java guide](docs/java.md)
- [Language parity matrix](docs/language-parity.md)
- [SonicOS quirks and gotchas](docs/sonicwall-quirks.md)
- [Endpoint support matrix](docs/endpoint-support-matrix.md)
- [Release readiness checklist](docs/release-readiness.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

## Live device validation (Python)

Copy the example env file (`.env` is gitignored):

```bash
cp .env.example .env
# edit .env with your lab appliance host, user, and password
```

Or export variables in your shell:

```bash
export SONICWALL_HOST="192.168.0.1"
export SONICWALL_USER="admin"
export SONICWALL_PASS="your-password"
```

From repo root:

```bash
./scripts/validate_local_device.sh
# destructive write CRUD (service/NAT/access-rule tests):
SONICWALL_INTEGRATION_WRITE=1 ./scripts/validate_local_device.sh --write
```

Or run pytest integration tests from `packages/python`:

```bash
cd packages/python
SONICWALL_HOST=... SONICWALL_PASS=... uv run pytest tests/integration -m integration -v
SONICWALL_INTEGRATION_WRITE=1 uv run pytest tests/integration -m integration_write -v
```

`SW_HOST` / `SW_PASS` are also accepted as aliases.

## Known Limitations

- Authentication parity is currently uneven across SDKs:
  - Python supports SonicOS 7.x Digest `auth-int` + bearer token flow.
  - TypeScript and Go currently target Basic + `smngsess` cookie variants.
  - Java currently targets Basic + `smngsess` cookie variants.
- Interface and DHCP endpoints vary by firmware and may be unavailable on some
  validated devices. See `docs/current-status.md` and `docs/sonicwall-quirks.md`.

## Repository layout

- **GitLab** (`gandiva-tech/sonicwall-sdk`): primary development (`dev` → `main`), CI, and releases.
- **GitHub** ([moolap/sonicwall-sdk](https://github.com/moolap/sonicwall-sdk)): public mirror of `main` and release tags. See [docs/mirroring.md](docs/mirroring.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). DCO sign-off required on all commits.

## Code of Conduct

All participants are expected to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

Apache-2.0. See [LICENSE](LICENSE).