from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, TypeVar

from cfboundary.ffi import d1_null, to_js, to_py

try:
    import js  # type: ignore[import-not-found]
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:
    js = None  # type: ignore[assignment]

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


T = TypeVar("T")


@dataclass(frozen=True)
class Quote:
    quote: str
    author: str


class D1Statement:
    """A prepared statement handle with Python-native result helpers."""

    def __init__(self, raw_statement: Any):
        self.raw = raw_statement

    def bind(self, *params: Any) -> D1Statement:
        return D1Statement(self.raw.bind(*[d1_null(param) for param in params]))

    async def all(self, *params: Any) -> list[dict[str, Any]]:
        statement = self.bind(*params) if params else self
        result = to_py(await statement.raw.all())
        return list(result.get("results", []))

    async def one(self, *params: Any) -> dict[str, Any] | None:
        rows = await self.all(*params)
        return rows[0] if rows else None

    async def one_as(self, factory: Callable[..., T], *params: Any) -> T | None:
        row = await self.one(*params)
        return None if row is None else factory(**row)


class D1Database:
    """Pythonic service wrapper over a D1 binding."""

    def __init__(self, raw: Any):
        self.raw = raw

    def statement(self, sql: str) -> D1Statement:
        return D1Statement(self.raw.prepare(sql))

    async def query(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        return await self.statement(sql).all(*params)

    async def query_one(self, sql: str, *params: Any) -> dict[str, Any] | None:
        return await self.statement(sql).one(*params)


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        db = D1Database(self.env.DB)
        quote = await db.statement(
            "SELECT quote, author FROM quotes ORDER BY RANDOM() LIMIT 1"
        ).one_as(Quote)
        return json_response(asdict(quote or Quote("No quotes yet", "D1")))


def json_response(data: Any) -> Any:
    if js is None:
        return {"body": data}
    return js.Response.new(
        json.dumps(data),
        to_js({"headers": {"content-type": "application/json"}}),
    )
