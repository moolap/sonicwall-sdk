# SonicWall SDK for Python

Python client for SonicOS REST API with async-first APIs, sync wrapper, pending
config transaction helpers, and typed exceptions.

## Install

```bash
pip install sonicwall-sdk
# or
uv add sonicwall-sdk
```

## Quick start (async)

```python
import asyncio
from sonicwall import SonicWallClient

async def main() -> None:
    async with SonicWallClient(
        host="192.168.1.1",
        username="admin",
        password="secret",
        verify_ssl=False,
    ) as client:
        objs = await client.address_objects.list()
        print(f"address objects: {len(objs)}")

asyncio.run(main())
```

## Authentication

On SonicOS 7.x, the SDK performs Digest `auth-int` login handshake on
`POST /auth`, then sends `Authorization: Bearer <token>` for authenticated API
calls. This is automatic; no manual auth header or cookie handling is needed.

## Transactions

SonicOS stages writes in pending config. Use `pending()` to auto-commit on
success and auto-rollback on exceptions:

```python
async with client.pending():
    await client.address_objects.create(obj)
```

## More docs

- Root guide: `README.md`
- Python guide: `docs/python.md`
- SonicOS quirks: `docs/sonicwall-quirks.md`
