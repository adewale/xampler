from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, cast

from cfboundary.ffi import to_js, to_py

from xampler.cloudflare import CloudflareService

ReturnMetadata = Literal["none", "indexed", "all"]
VECTOR_DIMENSIONS = 32


def unit_vector(index: int, *, dimensions: int = VECTOR_DIMENSIONS) -> list[float]:
    return [1.0 if position == index else 0.0 for position in range(dimensions)]


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


class VectorIndex(CloudflareService[Any]):
    """Pythonic service wrapper for a Vectorize index."""

    dimensions: int | None

    def __init__(self, raw: Any, *, dimensions: int | None = None):
        super().__init__(raw)
        object.__setattr__(self, "dimensions", dimensions)

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
        raw_data = to_py(await self.raw.queryById(vector_id, to_js({"topK": top_k})))
        return self._result(raw_data)

    async def query(self, query: VectorQuery) -> VectorQueryResult:
        self.validate(query.values)
        raw_data = to_py(await self.raw.query(to_js(query.values), to_js(query.options())))
        return self._result(raw_data)

    def _result(self, raw_data: Any) -> VectorQueryResult:
        data = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
        matches: list[VectorMatch] = []
        for raw_match in data.get("matches", []):
            if not isinstance(raw_match, dict):
                continue
            match = cast(dict[str, Any], raw_match)
            raw_metadata = match.get("metadata")
            raw_values = match.get("values")
            matches.append(
                VectorMatch(
                    id=str(match.get("id", "")),
                    score=float(match.get("score", 0.0)),
                    metadata=cast(dict[str, Any], raw_metadata)
                    if isinstance(raw_metadata, dict)
                    else None,
                    values=[float(value) for value in cast(list[Any], raw_values)]
                    if isinstance(raw_values, list)
                    else None,
                )
            )
        return VectorQueryResult(matches=matches)

    async def get(self, ids: list[str]) -> Any:
        return to_py(await self.raw.getByIds(to_js(ids)))

    async def delete(self, ids: list[str]) -> None:
        await self.raw.deleteByIds(to_js(ids))

    async def describe(self) -> Any:
        return to_py(await self.raw.describe())


class DemoVectorIndex:
    def __init__(
        self,
        dimensions: int = VECTOR_DIMENSIONS,
        *,
        keywords: tuple[str, ...] = ("hvsc", "sid", "commodore"),
    ):
        self.dimensions = dimensions
        self.keywords = keywords
        self.vectors = [
            Vector("doc-1", unit_vector(0, dimensions=dimensions), metadata={"url": "/docs/1"}),
            Vector("doc-2", unit_vector(1, dimensions=dimensions), metadata={"url": "/docs/2"}),
        ]

    def embed(self, text: str) -> list[float]:
        lowered = text.lower()
        values = [float(keyword in lowered) for keyword in self.keywords]
        return (values + [0.0] * self.dimensions)[: self.dimensions]

    def score(self, query: str, document: str) -> float:
        q = self.embed(query)
        d = self.embed(document)
        return sum(a * b for a, b in zip(q, d, strict=True))

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
            matches=sorted(matches, key=lambda match: match.score, reverse=True)[:top_k]
        )


__all__ = [
    "DemoVectorIndex",
    "ReturnMetadata",
    "VECTOR_DIMENSIONS",
    "Vector",
    "VectorIndex",
    "VectorMatch",
    "VectorQuery",
    "VectorQueryResult",
    "unit_vector",
]
