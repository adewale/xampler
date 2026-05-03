from __future__ import annotations

from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.hyperdrive import DemoPostgres, HyperdriveConfig, HyperdrivePostgres, PostgresQuery


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
