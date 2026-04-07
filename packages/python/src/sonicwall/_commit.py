"""Pending-config transaction context manager."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import TYPE_CHECKING

from ._exceptions import CommitError, RollbackError

if TYPE_CHECKING:
    from ._http import HTTPClient

logger = logging.getLogger(__name__)


class CommitContext:
    """Async context manager that wraps SonicOS pending-config transactions.

    Usage::

        async with client.pending():
            await client.address_objects.create(obj)
            await client.nat_policies.create(policy)
        # Commits on clean exit, rolls back on any exception

    Nesting:
        Nested ``pending()`` calls are no-ops — only the outermost context
        drives commit/rollback. This allows helper functions to use
        ``async with client.pending()`` safely even when called from within
        an outer transaction.
    """

    def __init__(self, http_client: "HTTPClient", *, depth_tracker: list[int]) -> None:
        self._http = http_client
        self._depth_tracker = depth_tracker

    async def __aenter__(self) -> "CommitContext":
        self._depth_tracker[0] += 1
        logger.debug("Entering pending-config context (depth=%d)", self._depth_tracker[0])
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self._depth_tracker[0] -= 1
        depth = self._depth_tracker[0]
        logger.debug("Exiting pending-config context (depth=%d, error=%s)", depth, exc_type)

        if depth > 0:
            # Still inside an outer pending() — let the outer handle commit/rollback
            return False

        if exc_type is None:
            # Clean exit — commit
            try:
                await self._http.request("POST", "/config/pending")
                logger.debug("Pending config committed successfully")
            except Exception as exc:
                raise CommitError(
                    f"Failed to commit pending configuration: {exc}"
                ) from exc
        else:
            # Exception — roll back
            try:
                await self._http.request("DELETE", "/config/pending")
                logger.debug("Pending config rolled back successfully")
            except Exception as exc:
                logger.error("Rollback failed: %s", exc)
                raise RollbackError(
                    f"Failed to roll back pending configuration: {exc}"
                ) from exc

        return False  # Do not suppress the original exception