from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.r2_data_catalog import DemoR2DataCatalog, R2DataCatalog


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path.startswith("/demo/tables/"):
            namespace = path.removeprefix("/demo/tables/")
            return Response.json(await DemoR2DataCatalog().list_tables(namespace))
        if path == "/demo":
            return Response.json(await DemoR2DataCatalog().list_namespaces())
        catalog = R2DataCatalog(uri=str(self.env.CATALOG_URI), token=str(self.env.CATALOG_TOKEN))
        if path.startswith("/tables/"):
            return Response.json(await catalog.list_tables(path.removeprefix("/tables/")))
        if path.startswith("/lifecycle/"):
            parts = path.removeprefix("/lifecycle/").split("/", 1)
            namespace, table = parts if len(parts) == 2 else ("xampler_verify", "temp_table")
            return Response.json(await catalog.lifecycle(namespace, table))
        return Response.json(await catalog.list_namespaces())
