from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal
from urllib.parse import urlparse

from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

ReturnMetadata = Literal["none", "indexed", "all"]


@dataclass(frozen=True)
class Vector:
    id: str
    values: list[float]
    namespace: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, kw_only=True)
class VectorQuery:
    values: list[float]
    top_k: int = 5
    return_metadata: ReturnMetadata = "indexed"
    return_values: bool = False
    namespace: str | None = None
    filter: dict[str, Any] | None = None

    def options(self) -> dict[str, Any]:
        return {
            "topK": self.top_k,
            "returnMetadata": self.return_metadata,
            "returnValues": self.return_values,
            **({"namespace": self.namespace} if self.namespace else {}),
            **({"filter": self.filter} if self.filter else {}),
        }


class VectorIndex:
    def __init__(self, raw: Any):
        self.raw = raw

    async def upsert(self, vectors: list[Vector]) -> Any:
        return to_py(await self.raw.upsert(to_js([asdict(v) for v in vectors])))

    async def query(self, query: VectorQuery) -> Any:
        return to_py(await self.raw.query(to_js(query.values), to_js(query.options())))

    async def get(self, ids: list[str]) -> Any:
        return to_py(await self.raw.getByIds(to_js(ids)))

    async def delete(self, ids: list[str]) -> None:
        await self.raw.deleteByIds(to_js(ids))

    async def describe(self) -> Any:
        return to_py(await self.raw.describe())


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        index = VectorIndex(self.env.INDEX)
        path = urlparse(str(request.url)).path
        if path == "/describe":
            return Response.json(await index.describe())
        if request.method == "POST" and path == "/upsert":
            data = to_py(await request.json())
            vector = Vector(**data)
            return Response.json(await index.upsert([vector]))
        if request.method == "POST" and path == "/query":
            data = to_py(await request.json())
            return Response.json(await index.query(VectorQuery(**data)))
        return Response("Use /describe, POST /upsert, or POST /query.\n")
