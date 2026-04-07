"""Base resource class with common HTTP helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from .._client import SonicWallClient

T = TypeVar("T")


class BaseResource:
    """Base class for all SonicOS API resources.

    Provides convenience wrappers around the HTTP client that handle the
    SonicOS list-unwrapping pattern and keep resource code concise.
    """

    def __init__(self, client: "SonicWallClient") -> None:
        self._client = client
        self._http = client._http_client  # noqa: SLF001

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._http.request("GET", path, params=params)

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return await self._http.request("POST", path, json=body)

    async def _put(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return await self._http.request("PUT", path, json=body)

    async def _delete(self, path: str) -> None:
        await self._http.request("DELETE", path)

    async def _list(
        self,
        path: str,
        list_key: str,
        item_key: str | None,
        model_class: type[T],
        from_api: str = "from_api_response",
    ) -> list[T]:
        """Fetch and parse a SonicOS list response.

        Args:
            path: API path, e.g. "/address-objects/ipv4"
            list_key: Top-level key in the response that contains the list,
                      e.g. "address_objects"
            item_key: If set, each list item is unwrapped by this key before
                      passing to the model parser. Set None to pass items as-is.
            model_class: Model class to instantiate via its from_api_response classmethod.
            from_api: Name of the classmethod to call on model_class.
        """
        response = await self._get(path)
        items: list[Any] = response.get(list_key, [])
        parser = getattr(model_class, from_api)

        result: list[T] = []
        for item in items:
            if item_key and item_key in item:
                result.append(parser(item))
            else:
                result.append(parser(item))
        return result