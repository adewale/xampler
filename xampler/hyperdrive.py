from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HyperdriveConfig:
    connection_string: str
    host: str | None = None
    port: int | None = None
    database: str | None = None
    user: str | None = None

    @classmethod
    def from_binding(cls, binding: Any) -> HyperdriveConfig:
        return cls(
            connection_string=str(getattr(binding, "connectionString", "")),
            host=str(getattr(binding, "host", "")) or None,
            port=int(getattr(binding, "port", 0) or 0) or None,
            database=str(getattr(binding, "database", "")) or None,
            user=str(getattr(binding, "user", "")) or None,
        )


@dataclass(frozen=True)
class PostgresQuery:
    sql: str
    params: tuple[Any, ...] = ()

    def validate_read_only(self) -> None:
        normalized = self.sql.strip().lower()
        if not normalized.startswith("select"):
            raise ValueError("demo route only accepts read-only SELECT queries")


@dataclass(frozen=True)
class PostgresResult:
    rows: list[dict[str, Any]]
    row_count: int
    source: str


class HyperdrivePostgres:
    def __init__(self, config: HyperdriveConfig):
        self.config = config
        self.raw = config

    async def query(self, query: PostgresQuery) -> PostgresResult:
        query.validate_read_only()
        raise RuntimeError("configure a Postgres client for deployed Hyperdrive queries")


class DemoPostgres:
    raw = None

    async def query(self, query: PostgresQuery) -> PostgresResult:
        query.validate_read_only()
        rows = [
            {"id": 1, "title": "Hyperdrive keeps Postgres close to Workers", "tag": "postgres"},
            {"id": 2, "title": "Use typed query objects and read-only guards", "tag": "python"},
        ]
        return PostgresResult(rows=rows, row_count=len(rows), source="demo-hyperdrive")
