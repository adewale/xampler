from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class CatalogNamespace:
    name: str


@dataclass(frozen=True)
class TableRef:
    namespace: str
    name: str
    format: str = "iceberg"


class R2DataCatalog:
    def __init__(self, *, uri: str, token: str):
        self.uri = uri.rstrip("/")
        self.token = token

    async def get_json(self, path: str) -> Any:
        response = await js.fetch(
            f"{self.uri}{path}",
            to_js({"headers": {"authorization": f"Bearer {self.token}"}}),
        )
        return to_py(await response.json())

    async def list_namespaces(self) -> Any:
        return await self.get_json("/v1/namespaces")

    async def list_tables(self, namespace: str) -> Any:
        return await self.get_json(f"/v1/namespaces/{namespace}/tables")


class DemoR2DataCatalog:
    raw = None

    async def list_namespaces(self) -> dict[str, Any]:
        return {
            "namespaces": [asdict(CatalogNamespace("hvsc")), asdict(CatalogNamespace("examples"))]
        }

    async def list_tables(self, namespace: str) -> dict[str, Any]:
        return {"tables": [asdict(TableRef(namespace=namespace, name="tracks"))]}


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
        return Response.json(await catalog.list_namespaces())
