"""Local doubles for Cloudflare bindings, backed by real engines where possible.

Behaviour was checked once against Miniflare 4 (the local D1/KV runtime used by
`wrangler dev`):

- D1 runs SQLite. ``all()``/``run()`` resolve to ``{"success", "meta", "results"}``;
  rows are column-name dicts; a bound ``None`` is SQL NULL; ``batch()`` is atomic,
  so one failing statement leaves no rows from the batch behind; an empty
  ``batch([])`` raises "No SQL statements detected".
- KV ``list()`` returns keys in byte order filtered by ``prefix``, at most
  ``limit`` per page, with ``list_complete`` and an opaque ``cursor`` for the
  next page; ``get()`` of a missing key is null.
"""

from __future__ import annotations

import sqlite3
from typing import Any


class SqliteD1Statement:
    def __init__(self, db: SqliteD1Binding, sql: str, params: tuple[Any, ...] = ()):
        self.db = db
        self.sql = sql
        self.params = params

    def bind(self, *params: Any) -> SqliteD1Statement:
        return SqliteD1Statement(self.db, self.sql, params)

    def _execute(self) -> dict[str, Any]:
        cursor = self.db.connection.execute(self.sql, self.params)
        columns = [column[0] for column in cursor.description or ()]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        return {"success": True, "meta": {"changes": cursor.rowcount}, "results": rows}

    async def all(self) -> dict[str, Any]:
        with self.db.connection:
            return self._execute()

    async def run(self) -> dict[str, Any]:
        return await self.all()


class SqliteD1Binding:
    """D1 binding over an in-memory SQLite database."""

    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:", isolation_level="DEFERRED")

    def prepare(self, sql: str) -> SqliteD1Statement:
        return SqliteD1Statement(self, sql)

    async def batch(self, statements: list[SqliteD1Statement]) -> list[dict[str, Any]]:
        if not statements:
            raise RuntimeError("D1_ERROR: No SQL statements detected.")
        with self.connection:
            return [statement._execute() for statement in statements]


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
        names = sorted(name for name in self.values if name.startswith(options.get("prefix", "")))
        start = int(options.get("cursor", 0))
        limit = int(options.get("limit", 1000))
        page = names[start : start + limit]
        result: dict[str, Any] = {
            "keys": [{"name": name} for name in page],
            "list_complete": start + limit >= len(names),
        }
        if not result["list_complete"]:
            result["cursor"] = str(start + limit)
        return result
