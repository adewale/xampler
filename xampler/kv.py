from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, cast

from cfboundary.ffi import is_js_missing, to_js, to_py

from xampler.cloudflare import CloudflareService, ResourceRef


@dataclass(frozen=True)
class KVListResult:
    keys: list[str]
    cursor: str | None = None
    complete: bool = True


class KVNamespace(CloudflareService[Any]):
    def key(self, name: str) -> KVKey:
        return KVKey(name=name, namespace=self)

    async def list(
        self,
        *,
        prefix: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> KVListResult:
        options = {
            k: v
            for k, v in {"prefix": prefix, "limit": limit, "cursor": cursor}.items()
            if v is not None
        }
        raw_data = to_py(await self.raw.list(to_js(options)))
        data = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
        raw_keys = data.get("keys", [])
        key_items = cast(list[Any], raw_keys) if isinstance(raw_keys, list) else []
        keys = [
            str(cast(dict[str, Any], item).get("name"))
            for item in key_items
            if isinstance(item, dict)
        ]
        raw_cursor = data.get("cursor")
        return KVListResult(
            keys=keys,
            cursor=str(raw_cursor) if raw_cursor is not None else None,
            complete=not bool(data.get("list_complete") is False),
        )

    async def iter_keys(
        self,
        *,
        prefix: str | None = None,
        page_size: int = 1000,
    ) -> AsyncIterator[KVKey]:
        cursor: str | None = None
        while True:
            page = await self.list(prefix=prefix, limit=page_size, cursor=cursor)
            for name in page.keys:
                yield self.key(name)
            if page.complete:
                break
            cursor = page.cursor


class KVKey(ResourceRef[Any]):
    namespace: KVNamespace

    def __init__(self, namespace: KVNamespace, name: str):
        super().__init__(name=name, raw=namespace.raw)
        self.namespace = namespace

    async def get_text(self) -> str | None:
        return await self.read_text()

    async def put_text(self, value: str, *, expiration_ttl: int | None = None) -> None:
        await self.write_text(value, expiration_ttl=expiration_ttl)

    async def read_text(self) -> str | None:
        value = await self.namespace.raw.get(self.name)
        return None if is_js_missing(value) else str(value)

    async def write_text(self, value: str, *, expiration_ttl: int | None = None) -> None:
        options = {"expirationTtl": expiration_ttl} if expiration_ttl is not None else None
        if options:
            await self.namespace.raw.put(self.name, value, to_js(options))
        else:
            await self.namespace.raw.put(self.name, value)

    async def get_json(self) -> Any | None:
        return await self.read_json()

    async def put_json(self, value: Any, *, expiration_ttl: int | None = None) -> None:
        await self.write_json(value, expiration_ttl=expiration_ttl)

    async def read_json(self) -> Any | None:
        text = await self.read_text()
        return None if text is None else json.loads(text)

    async def write_json(self, value: Any, *, expiration_ttl: int | None = None) -> None:
        await self.write_text(json.dumps(value), expiration_ttl=expiration_ttl)

    async def exists(self) -> bool:
        return await self.read_text() is not None

    async def delete(self) -> None:
        await self.namespace.raw.delete(self.name)


__all__ = ["KVKey", "KVListResult", "KVNamespace"]
