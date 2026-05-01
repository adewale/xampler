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


@dataclass(frozen=True)
class VectorMatch:
    id: str
    score: float
    metadata: dict[str, Any] | None = None
    values: list[float] | None = None


@dataclass(frozen=True)
class VectorQueryResult:
    matches: list[VectorMatch]


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
    """Pythonic service wrapper for a Vectorize index."""

    def __init__(self, raw: Any, *, dimensions: int | None = None):
        self.raw = raw
        self.dimensions = dimensions

    def validate(self, values: list[float]) -> None:
        if self.dimensions is not None and len(values) != self.dimensions:
            raise ValueError(f"expected {self.dimensions} dimensions, got {len(values)}")

    async def upsert(self, vectors: list[Vector]) -> Any:
        for vector in vectors:
            self.validate(vector.values)
        return to_py(await self.raw.upsert(to_js([asdict(v) for v in vectors])))

    async def search(self, values: list[float], *, top_k: int = 5) -> VectorQueryResult:
        return await self.query(VectorQuery(values=values, top_k=top_k))

    async def query_by_id(self, vector_id: str, *, top_k: int = 5) -> VectorQueryResult:
        data = to_py(await self.raw.queryById(vector_id, to_js({"topK": top_k})))
        return self._result(data)

    async def query(self, query: VectorQuery) -> VectorQueryResult:
        self.validate(query.values)
        data = to_py(await self.raw.query(to_js(query.values), to_js(query.options())))
        return self._result(data)

    def _result(self, data: dict[str, Any]) -> VectorQueryResult:
        return VectorQueryResult(
            matches=[
                VectorMatch(
                    id=str(match["id"]),
                    score=float(match["score"]),
                    metadata=match.get("metadata"),
                    values=match.get("values"),
                )
                for match in data.get("matches", [])
            ]
        )

    async def get(self, ids: list[str]) -> Any:
        return to_py(await self.raw.getByIds(to_js(ids)))

    async def delete(self, ids: list[str]) -> None:
        await self.raw.deleteByIds(to_js(ids))

    async def describe(self) -> Any:
        return to_py(await self.raw.describe())


class DemoVectorIndex:
    def __init__(self, dimensions: int = 3):
        self.dimensions = dimensions
        self.vectors = [
            Vector("doc-1", [1.0, 0.0, 0.0], metadata={"url": "/docs/1"}),
            Vector("doc-2", [0.0, 1.0, 0.0], metadata={"url": "/docs/2"}),
        ]

    async def search(self, values: list[float], *, top_k: int = 5) -> VectorQueryResult:
        if len(values) != self.dimensions:
            raise ValueError(f"expected {self.dimensions} dimensions, got {len(values)}")
        matches = [
            VectorMatch(
                id=v.id,
                score=sum(a * b for a, b in zip(values, v.values, strict=True)),
                metadata=v.metadata,
            )
            for v in self.vectors
        ]
        return VectorQueryResult(
            matches=sorted(matches, key=lambda m: m.score, reverse=True)[:top_k]
        )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        index = VectorIndex(self.env.INDEX)
        path = urlparse(str(request.url)).path
        if path == "/demo":
            result = await DemoVectorIndex().search([1.0, 0.0, 0.0], top_k=1)
            return Response.json(asdict(result))
        if path == "/describe":
            return Response.json(await index.describe())
        if request.method == "POST" and path == "/upsert":
            data = to_py(await request.json())
            vector = Vector(**data)
            return Response.json(await index.upsert([vector]))
        if request.method == "POST" and path == "/query":
            data = to_py(await request.json())
            result = await index.query(VectorQuery(**data))
            return Response.json(asdict(result))
        return Response("Use /describe, POST /upsert, or POST /query.\n")
