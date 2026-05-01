from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from cfboundary.ffi import d1_null, to_js, to_py

try:
    import js  # type: ignore[import-not-found]
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:
    js = None  # type: ignore[assignment]

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


@dataclass(frozen=True)
class Quote:
    quote: str
    author: str


class D1Database:
    def __init__(self, raw: Any):
        self.raw = raw

    async def query(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        stmt = self.raw.prepare(sql)
        if params:
            stmt = stmt.bind(*[d1_null(p) for p in params])
        result = to_py(await stmt.all())
        return list(result.get("results", []))

    async def query_one(self, sql: str, *params: Any) -> dict[str, Any] | None:
        rows = await self.query(sql, *params)
        return rows[0] if rows else None


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        db = D1Database(self.env.DB)
        row = await db.query_one("SELECT quote, author FROM quotes ORDER BY RANDOM() LIMIT 1")
        quote = Quote(**row) if row else Quote("No quotes yet", "D1")
        return json_response(asdict(quote))


def json_response(data: Any) -> Any:
    if js is None:
        return {"body": data}
    return js.Response.new(
        json.dumps(data),
        to_js({"headers": {"content-type": "application/json"}}),
    )
