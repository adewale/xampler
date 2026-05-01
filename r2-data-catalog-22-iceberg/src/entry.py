from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class Namespace:
    name: str


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


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        catalog = R2DataCatalog(uri=str(self.env.CATALOG_URI), token=str(self.env.CATALOG_TOKEN))
        path = urlparse(str(request.url)).path
        if path.startswith("/tables/"):
            return Response.json(await catalog.list_tables(path.removeprefix("/tables/")))
        return Response.json(await catalog.list_namespaces())
