from __future__ import annotations

from typing import Any, TypeVar

from .cloudflare import CloudflareService, ResourceRef

RefT = TypeVar("RefT", bound="DurableObjectRef")


class DurableObjectRef(ResourceRef[Any]):
    """Typed handle around one Durable Object stub."""

    name: str

    def __init__(self, name: str, raw_stub: Any):
        super().__init__(name=name, raw=raw_stub)

    async def fetch(self, request: Any) -> Any:
        return await self.raw.fetch(request)

    async def fetch_path(self, path: str = "/") -> Any:
        normalized = path if path.startswith("/") else f"/{path}"
        return await self.raw.fetch(f"https://durable-object.local/{self.name}{normalized}")

    async def text(self, path: str = "/") -> str:
        response = await self.fetch_path(path)
        return str(await response.text())


class DurableObjectNamespace[RefT: DurableObjectRef](CloudflareService[Any]):
    """Pythonic wrapper around a Durable Object namespace binding."""

    ref_type: type[RefT]

    def __init__(self, raw: Any, *, ref_type: type[RefT] | None = None):
        super().__init__(raw)
        self.ref_type = ref_type or DurableObjectRef  # type: ignore[assignment]

    def named(self, name: str) -> RefT:
        return self.ref_type(name, self.raw.get(self.raw.idFromName(name)))

    def id(self, name: str) -> Any:
        return self.raw.idFromName(name)
