"""Local doubles for Cloudflare bindings, backed by real engines where possible.

Behaviour was checked once against Miniflare 4 (the local D1/KV runtime used by
`wrangler dev`):

- D1 runs SQLite. ``all()``/``run()`` resolve to ``{"success", "meta", "results"}``;
  rows are column-name dicts; a bound ``None`` is SQL NULL; a Python int reaches
  D1 as a JS number and binds as REAL (ints beyond 2**53 become BigInt, which D1
  rejects); empty or blank SQL raises "No SQL statements detected", and so does
  an empty ``batch([])``; ``batch()`` is atomic, DDL included.
- KV ``list()`` returns keys in byte order filtered by ``prefix``, at most
  ``limit`` (default and maximum 1000) per page, with ``list_complete`` and an
  opaque ``cursor`` that resumes after the last key returned, even if earlier keys
  were deleted meanwhile; ``get()`` of a missing key is null.
"""

from __future__ import annotations

import sqlite3
from typing import Any


def _js_number(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, int):
        return value
    if abs(value) > 2**53:
        raise TypeError("D1_TYPE_ERROR: Type 'bigint' not supported")
    return float(value)


class SqliteD1Statement:
    def __init__(self, db: SqliteD1Binding, sql: str, params: tuple[Any, ...] = ()):
        self.db = db
        self.sql = sql
        self.params = params

    def bind(self, *params: Any) -> SqliteD1Statement:
        return SqliteD1Statement(self.db, self.sql, tuple(_js_number(param) for param in params))

    def _execute(self) -> dict[str, Any]:
        if not self.sql.strip():
            raise RuntimeError("D1_ERROR: No SQL statements detected.")
        cursor = self.db.connection.execute(self.sql, self.params)
        columns = [column[0] for column in cursor.description or ()]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        return {"success": True, "meta": {"changes": max(cursor.rowcount, 0)}, "results": rows}

    async def all(self) -> dict[str, Any]:
        return self._execute()

    async def run(self) -> dict[str, Any]:
        return await self.all()


class SqliteD1Binding:
    """D1 binding over an in-memory SQLite database."""

    def __init__(self) -> None:
        # Autocommit, like single D1 statements; batch() opens its own transaction.
        self.connection = sqlite3.connect(":memory:", isolation_level=None)

    def prepare(self, sql: str) -> SqliteD1Statement:
        return SqliteD1Statement(self, sql)

    async def batch(self, statements: list[SqliteD1Statement]) -> list[dict[str, Any]]:
        if not statements:
            raise RuntimeError("D1_ERROR: No SQL statements detected.")
        self.connection.execute("BEGIN")
        try:
            results = [statement._execute() for statement in statements]
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise
        self.connection.execute("COMMIT")
        return results


class PagingKVBinding:
    """KV binding with real list paging; records the options passed to put()."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.put_options: dict[str, Any] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def put(self, key: str, value: str, options: Any | None = None) -> None:
        self.values[key] = value
        self.put_options[key] = options

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def list(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        options = options or {}
        limit = int(options.get("limit") or 1000)
        if limit > 1000:
            raise ValueError("Invalid key_count_limit: must be at most 1000")
        names = sorted(name for name in self.values if name.startswith(options.get("prefix", "")))
        after = options.get("cursor")
        if after is not None:
            names = [name for name in names if name > after]
        page = names[:limit]
        result: dict[str, Any] = {
            "keys": [{"name": name} for name in page],
            "list_complete": len(names) <= limit,
        }
        if not result["list_complete"]:
            result["cursor"] = page[-1]
        return result
