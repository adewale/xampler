from __future__ import annotations

from typing import Any
from urllib.parse import unquote, urlsplit

from cfboundary.ffi import to_py

from xampler.kv import KVNamespace
from xampler.response import json_response, text_response

try:
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


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
