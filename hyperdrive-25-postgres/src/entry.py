from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


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
        # A deployed Worker would create a Postgres client with
        # self.config.connection_string here. The deterministic demo transport
        # below keeps local verification account-free.
        raise RuntimeError("configure a Postgres client for deployed Hyperdrive queries")


class DemoPostgres:
    def __init__(self) -> None:
        self.raw = None

    async def query(self, query: PostgresQuery) -> PostgresResult:
        query.validate_read_only()
        rows = [
            {"id": 1, "title": "Hyperdrive keeps Postgres close to Workers", "tag": "postgres"},
            {"id": 2, "title": "Use typed query objects and read-only guards", "tag": "python"},
        ]
        return PostgresResult(rows=rows, row_count=len(rows), source="demo-hyperdrive")


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/demo":
            result = await DemoPostgres().query(PostgresQuery("SELECT * FROM notes"))
            return Response.json(asdict(result))
        if path == "/config":
            return Response.json(asdict(HyperdriveConfig.from_binding(self.env.HYPERDRIVE)))
        if path == "/query":
            client = HyperdrivePostgres(HyperdriveConfig.from_binding(self.env.HYPERDRIVE))
            try:
                result = await client.query(PostgresQuery("SELECT now()"))
                return Response.json(asdict(result))
            except Exception as exc:  # noqa: BLE001 - tutorial route returns setup guidance.
                return Response.json({"error": str(exc), "hint": "use /demo locally"}, status=501)
        return Response("Hyperdrive Postgres example. Try /demo or /config.")
