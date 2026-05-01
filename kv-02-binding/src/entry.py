from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit

from cfboundary.ffi import is_js_missing, to_js, to_py

try:
    import js  # type: ignore[import-not-found]
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:
    js = None  # type: ignore[assignment]

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


@dataclass(frozen=True)
class KVListResult:
    keys: list[str]
    cursor: str | None = None
    complete: bool = True


class KVNamespace:
    def __init__(self, raw: Any):
        self.raw = raw

    def key(self, name: str) -> KVKey:
        return KVKey(self, name)

    async def list(self, *, prefix: str | None = None, limit: int | None = None) -> KVListResult:
        options = {k: v for k, v in {"prefix": prefix, "limit": limit}.items() if v is not None}
        data = to_py(await self.raw.list(to_js(options)))
        return KVListResult(
            keys=[item["name"] for item in data.get("keys", [])],
            cursor=data.get("cursor"),
            complete=not bool(data.get("list_complete") is False),
        )


class KVKey:
    def __init__(self, namespace: KVNamespace, name: str):
        self.namespace = namespace
        self.name = name

    async def read_text(self) -> str | None:
        value = await self.namespace.raw.get(self.name)
        return None if is_js_missing(value) else str(value)

    async def write_text(self, value: str, *, expiration_ttl: int | None = None) -> None:
        options = {"expirationTtl": expiration_ttl} if expiration_ttl is not None else None
        if options:
            await self.namespace.raw.put(self.name, value, to_js(options))
        else:
            await self.namespace.raw.put(self.name, value)

    async def read_json(self) -> Any | None:
        text = await self.read_text()
        return None if text is None else json.loads(text)

    async def write_json(self, value: Any, *, expiration_ttl: int | None = None) -> None:
        await self.write_text(json.dumps(value), expiration_ttl=expiration_ttl)

    async def exists(self) -> bool:
        return await self.read_text() is not None

    async def delete(self) -> None:
        await self.namespace.raw.delete(self.name)


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        kv = KVNamespace(self.env.KV)
        method, path = str(request.method).upper(), urlsplit(str(request.url)).path
        if method == "GET" and path == "/keys":
            result = await kv.list()
            return json_response(result.__dict__)
        if key := _key(path, "/text/"):
            item = kv.key(key)
            if method == "PUT":
                await item.write_text(await request.text())
                return text_response("stored", status=201)
            value = await item.read_text()
            return text_response(value or "not found", status=200 if value is not None else 404)
        if key := _key(path, "/json/"):
            item = kv.key(key)
            if method == "PUT":
                await item.write_json(to_py(await request.json()))
                return text_response("stored", status=201)
            value = await item.read_json()
            return json_response(value, status=200 if value is not None else 404)
        if key := _key(path, "/keys/"):
            await kv.key(key).delete()
            return text_response("deleted")
        return text_response("not found", status=404)


def _key(path: str, prefix: str) -> str | None:
    return unquote(path[len(prefix):]) if path.startswith(prefix) else None

def text_response(body: str, *, status: int = 200) -> Any:
    return response(body, status=status, content_type="text/plain")

def json_response(body: Any, *, status: int = 200) -> Any:
    return response(json.dumps(body), status=status, content_type="application/json")

def response(body: Any, *, status: int = 200, content_type: str = "text/plain") -> Any:
    if js is None:
        return {"body": body, "status": status, "headers": {"content-type": content_type}}
    return js.Response.new(
        body,
        to_js({"status": status, "headers": {"content-type": content_type}}),
    )
