"""SonicWall async and sync client."""

from __future__ import annotations

import asyncio
import threading
from types import TracebackType
from typing import TYPE_CHECKING

import anyio
import anyio.from_thread

from ._auth import AuthManager
from ._commit import CommitContext
from ._exceptions import CommitError, RollbackError
from ._http import HTTPClient

if TYPE_CHECKING:
    from .resources.access_rules import AccessRulesResource
    from .resources.address_objects import AddressObjectsResource
    from .resources.dhcp import DhcpResource
    from .resources.interfaces import InterfacesResource
    from .resources.nat_policies import NatPoliciesResource
    from .resources.service_objects import ServiceObjectsResource


class SonicWallClient:
    """Async SonicWall API client.

    Usage::

        async with SonicWallClient("192.168.1.1", "admin", "pass") as client:
            objs = await client.address_objects.list()

    Or manually::

        client = SonicWallClient("192.168.1.1", "admin", "pass")
        await client.connect()
        try:
            ...
        finally:
            await client.disconnect()
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        verify_ssl: bool = False,
        timeout: float = 30.0,
        auto_commit: bool = False,
    ) -> None:
        scheme = "https"
        base_url = f"{scheme}://{host}/api/sonicos"
        self._auto_commit = auto_commit
        self._auth = AuthManager(base_url, username, password)
        self._http = HTTPClient(
            base_url,
            self._auth,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )
        # Depth counter for nested pending() calls; stored as list so CommitContext
        # can mutate it by reference.
        self._pending_depth: list[int] = [0]

        # Lazily initialised resource singletons
        self._address_objects: AddressObjectsResource | None = None
        self._access_rules: AccessRulesResource | None = None
        self._interfaces: InterfacesResource | None = None
        self._nat_policies: NatPoliciesResource | None = None
        self._service_objects: ServiceObjectsResource | None = None
        self._dhcp: DhcpResource | None = None

    # --- Lifecycle ---

    async def connect(self) -> None:
        """Authenticate and establish a session."""
        await self._auth.authenticate(self._http._client)  # noqa: SLF001

    async def disconnect(self) -> None:
        """Log out and close the HTTP connection."""
        await self._auth.logout(self._http._client)  # noqa: SLF001
        await self._http.aclose()

    async def __aenter__(self) -> "SonicWallClient":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.disconnect()

    # --- Commit / Rollback ---

    async def commit(self) -> None:
        """Commit all staged (pending) configuration changes."""
        try:
            await self._http.request("POST", "/config/pending")
        except Exception as exc:
            raise CommitError(f"Commit failed: {exc}") from exc

    async def rollback(self) -> None:
        """Roll back all staged (pending) configuration changes."""
        try:
            await self._http.request("DELETE", "/config/pending")
        except Exception as exc:
            raise RollbackError(f"Rollback failed: {exc}") from exc

    def pending(self) -> CommitContext:
        """Return a context manager that commits on clean exit and rolls back on error.

        Nested calls are no-ops (the outermost pending() owns the transaction).
        """
        return CommitContext(self._http, depth_tracker=self._pending_depth)

    # --- Resources (lazy singletons) ---

    @property
    def address_objects(self) -> "AddressObjectsResource":
        if self._address_objects is None:
            from .resources.address_objects import AddressObjectsResource
            self._address_objects = AddressObjectsResource(self)
        return self._address_objects

    @property
    def access_rules(self) -> "AccessRulesResource":
        if self._access_rules is None:
            from .resources.access_rules import AccessRulesResource
            self._access_rules = AccessRulesResource(self)
        return self._access_rules

    @property
    def interfaces(self) -> "InterfacesResource":
        if self._interfaces is None:
            from .resources.interfaces import InterfacesResource
            self._interfaces = InterfacesResource(self)
        return self._interfaces

    @property
    def nat_policies(self) -> "NatPoliciesResource":
        if self._nat_policies is None:
            from .resources.nat_policies import NatPoliciesResource
            self._nat_policies = NatPoliciesResource(self)
        return self._nat_policies

    @property
    def service_objects(self) -> "ServiceObjectsResource":
        if self._service_objects is None:
            from .resources.service_objects import ServiceObjectsResource
            self._service_objects = ServiceObjectsResource(self)
        return self._service_objects

    @property
    def dhcp(self) -> "DhcpResource":
        if self._dhcp is None:
            from .resources.dhcp import DhcpResource
            self._dhcp = DhcpResource(self)
        return self._dhcp

    # --- Internal HTTP accessor for resources ---

    @property
    def _http_client(self) -> HTTPClient:
        return self._http


class SonicWallClientSync:
    """Synchronous wrapper around SonicWallClient.

    Runs an asyncio event loop in a background thread and exposes all
    async methods as blocking calls. Suitable for scripts, CLIs, and
    environments where async is not available.

    Usage::

        with SonicWallClientSync("192.168.1.1", "admin", "pass") as client:
            objs = client.address_objects.list()
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        verify_ssl: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self._async_client = SonicWallClient(
            host,
            username,
            password,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def _start_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run(self, coro: object) -> object:  # type: ignore[type-arg]
        """Submit a coroutine to the background event loop and wait for result."""
        import concurrent.futures
        assert self._loop is not None
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)  # type: ignore[arg-type]
        return future.result()

    def connect(self) -> None:
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()
        # Wait until the loop is actually running
        while self._loop is None or not self._loop.is_running():
            import time
            time.sleep(0.01)
        self._run(self._async_client.connect())

    def disconnect(self) -> None:
        self._run(self._async_client.disconnect())
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def __enter__(self) -> "SonicWallClientSync":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.disconnect()

    def commit(self) -> None:
        self._run(self._async_client.commit())

    def rollback(self) -> None:
        self._run(self._async_client.rollback())

    @property
    def address_objects(self) -> "_SyncAddressObjectsResource":
        return _SyncAddressObjectsResource(self._async_client.address_objects, self._run)

    @property
    def access_rules(self) -> "_SyncAccessRulesResource":
        return _SyncAccessRulesResource(self._async_client.access_rules, self._run)

    @property
    def interfaces(self) -> "_SyncInterfacesResource":
        return _SyncInterfacesResource(self._async_client.interfaces, self._run)

    @property
    def nat_policies(self) -> "_SyncNatPoliciesResource":
        return _SyncNatPoliciesResource(self._async_client.nat_policies, self._run)

    @property
    def service_objects(self) -> "_SyncServiceObjectsResource":
        return _SyncServiceObjectsResource(self._async_client.service_objects, self._run)

    @property
    def dhcp(self) -> "_SyncDhcpResource":
        return _SyncDhcpResource(self._async_client.dhcp, self._run)


# ---------------------------------------------------------------------------
# Sync resource shims
# ---------------------------------------------------------------------------

from typing import Any, Callable  # noqa: E402


class _SyncResourceBase:
    def __init__(self, async_resource: Any, run: Callable[..., Any]) -> None:
        self._async = async_resource
        self._run = run


class _SyncAddressObjectsResource(_SyncResourceBase):
    def list(self) -> Any:
        return self._run(self._async.list())

    def get(self, name: str) -> Any:
        return self._run(self._async.get(name))

    def create(self, obj: Any) -> Any:
        return self._run(self._async.create(obj))

    def update(self, name: str, obj: Any) -> Any:
        return self._run(self._async.update(name, obj))

    def delete(self, name: str) -> None:
        self._run(self._async.delete(name))

    def ensure(self, obj: Any) -> Any:
        return self._run(self._async.ensure(obj))


class _SyncAccessRulesResource(_SyncResourceBase):
    def list(self) -> Any:
        return self._run(self._async.list())

    def get(self, from_zone: str, to_zone: str, name: str) -> Any:
        return self._run(self._async.get(from_zone, to_zone, name))

    def create(self, obj: Any) -> Any:
        return self._run(self._async.create(obj))

    def update(self, from_zone: str, to_zone: str, name: str, obj: Any) -> Any:
        return self._run(self._async.update(from_zone, to_zone, name, obj))

    def delete(self, from_zone: str, to_zone: str, name: str) -> None:
        self._run(self._async.delete(from_zone, to_zone, name))


class _SyncInterfacesResource(_SyncResourceBase):
    def list(self) -> Any:
        return self._run(self._async.list())

    def get(self, name: str) -> Any:
        return self._run(self._async.get(name))


class _SyncNatPoliciesResource(_SyncResourceBase):
    def list(self) -> Any:
        return self._run(self._async.list())

    def get(self, name: str) -> Any:
        return self._run(self._async.get(name))

    def create(self, obj: Any) -> Any:
        return self._run(self._async.create(obj))

    def update(self, name: str, obj: Any) -> Any:
        return self._run(self._async.update(name, obj))

    def delete(self, name: str) -> None:
        self._run(self._async.delete(name))


class _SyncServiceObjectsResource(_SyncResourceBase):
    def list(self) -> Any:
        return self._run(self._async.list())

    def get(self, name: str) -> Any:
        return self._run(self._async.get(name))

    def create(self, obj: Any) -> Any:
        return self._run(self._async.create(obj))

    def update(self, name: str, obj: Any) -> Any:
        return self._run(self._async.update(name, obj))

    def delete(self, name: str) -> None:
        self._run(self._async.delete(name))


class _SyncDhcpResource(_SyncResourceBase):
    def list_leases(self) -> Any:
        return self._run(self._async.list_leases())