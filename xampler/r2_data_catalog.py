from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from cfboundary.ffi import to_js, to_py

from xampler.cloudflare import RestClient

try:
    import js  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    js = None  # type: ignore[assignment]


@dataclass(frozen=True)
class CatalogNamespace:
    name: str


@dataclass(frozen=True)
class TableRef:
    namespace: str
    name: str
    format: str = "iceberg"


class R2DataCatalog(RestClient[Any]):
    token: str

    def __init__(self, *, uri: str, token: str):
        super().__init__(raw=None, base_url=uri.rstrip("/"))
        object.__setattr__(self, "token", token)

    async def request_json(
        self, path: str, *, method: str = "GET", payload: dict[str, Any] | None = None
    ) -> Any:
        if js is None:
            raise RuntimeError("R2DataCatalog requires the Workers runtime js module")
        response = await js.fetch(
            f"{self.base_url}{path}",
            to_js({
                "method": method,
                "headers": {
                    "authorization": f"Bearer {self.token}",
                    "content-type": "application/json",
                },
                **({"body": json.dumps(payload)} if payload is not None else {}),
            }),
        )
        if int(response.status) == 204:
            return {"status": 204}
        return to_py(await response.json())

    async def list_namespaces(self) -> Any:
        return await self.request_json("/v1/namespaces")

    async def create_namespace(self, namespace: str) -> Any:
        return await self.request_json(
            "/v1/namespaces", method="POST", payload={"namespace": [namespace]}
        )

    async def delete_namespace(self, namespace: str) -> Any:
        return await self.request_json(f"/v1/namespaces/{namespace}", method="DELETE")

    async def list_tables(self, namespace: str) -> Any:
        return await self.request_json(f"/v1/namespaces/{namespace}/tables")

    async def create_table(self, namespace: str, table: str) -> Any:
        return await self.request_json(
            f"/v1/namespaces/{namespace}/tables",
            method="POST",
            payload={
                "name": table,
                "schema": {
                    "type": "struct",
                    "schema-id": 0,
                    "fields": [
                        {"id": 1, "name": "id", "required": True, "type": "int"},
                        {"id": 2, "name": "text", "required": False, "type": "string"},
                    ],
                },
            },
        )

    async def delete_table(self, namespace: str, table: str) -> Any:
        return await self.request_json(
            f"/v1/namespaces/{namespace}/tables/{table}", method="DELETE"
        )

    async def lifecycle(self, namespace: str, table: str) -> dict[str, Any]:
        created_namespace = await self.create_namespace(namespace)
        created_table = await self.create_table(namespace, table)
        tables = await self.list_tables(namespace)
        deleted_table = await self.delete_table(namespace, table)
        deleted_namespace = await self.delete_namespace(namespace)
        return {
            "namespace": namespace,
            "table": table,
            "created_namespace": created_namespace,
            "created_table": created_table,
            "tables_after_create": tables,
            "deleted_table": deleted_table,
            "deleted_namespace": deleted_namespace,
            "lifecycle_complete": True,
        }


class DemoR2DataCatalog:
    raw = None

    async def list_namespaces(self) -> dict[str, Any]:
        return {
            "namespaces": [asdict(CatalogNamespace("hvsc")), asdict(CatalogNamespace("examples"))]
        }

    async def list_tables(self, namespace: str) -> dict[str, Any]:
        return {"tables": [asdict(TableRef(namespace=namespace, name="tracks"))]}

    async def lifecycle(self, namespace: str, table: str) -> dict[str, Any]:
        return {
            "namespace": namespace,
            "table": table,
            "tables_after_create": await self.list_tables(namespace),
            "lifecycle_complete": True,
            "demo": True,
        }


__all__ = [
    "CatalogNamespace",
    "DemoR2DataCatalog",
    "R2DataCatalog",
    "TableRef",
]
