from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

from cfboundary.ffi import d1_null, to_py

from xampler.cloudflare import CloudflareService

T = TypeVar("T")


class D1Statement:
    """Prepared statement handle with Python-native result helpers."""

    def __init__(self, raw_statement: Any):
        self.raw = raw_statement

    def bind(self, *params: Any) -> D1Statement:
        return D1Statement(self.raw.bind(*[d1_null(param) for param in params]))

    async def run(self, *params: Any) -> dict[str, Any]:
        statement = self.bind(*params) if params else self
        result = to_py(await statement.raw.run())
        return cast(dict[str, Any], result) if isinstance(result, dict) else {}

    async def all(self, *params: Any) -> list[dict[str, Any]]:
        statement = self.bind(*params) if params else self
        result = to_py(await statement.raw.all())
        data = cast(dict[str, Any], result) if isinstance(result, dict) else {}
        raw_rows = data.get("results", [])
        if not isinstance(raw_rows, list):
            return []
        rows = cast(list[Any], raw_rows)
        return [cast(dict[str, Any], row) for row in rows if isinstance(row, dict)]

    async def one(self, *params: Any) -> dict[str, Any] | None:
        rows = await self.all(*params)
        return rows[0] if rows else None

    async def first(self, *params: Any) -> dict[str, Any] | None:
        return await self.one(*params)

    async def one_as(self, factory: Callable[..., T], *params: Any) -> T | None:
        row = await self.one(*params)
        return None if row is None else factory(**row)


class D1Database(CloudflareService[Any]):
    """Pythonic service wrapper over a D1 binding."""

    def statement(self, sql: str) -> D1Statement:
        return D1Statement(self.raw.prepare(sql))

    async def execute(self, sql: str) -> None:
        for statement in [part.strip() for part in sql.split(";") if part.strip()]:
            await self.statement(statement).run()

    async def batch_run(self, statements: list[D1Statement]) -> None:
        if statements:
            from cfboundary.ffi import to_js

            await self.raw.batch(to_js([statement.raw for statement in statements]))

    async def query(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        return await self.statement(sql).all(*params)

    async def query_one(self, sql: str, *params: Any) -> dict[str, Any] | None:
        return await self.statement(sql).one(*params)


__all__ = ["D1Database", "D1Statement"]
