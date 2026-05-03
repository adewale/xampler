from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from cfboundary.ffi import to_js, to_py

from xampler.cloudflare import RestClient

try:
    import js  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    js = None  # type: ignore[assignment]


@dataclass(frozen=True)
class R2SqlQuery:
    sql: str

    def safe_sql(self) -> str:
        statement = self.sql.strip().rstrip(";")
        lowered = statement.lower()
        forbidden = (" insert ", " update ", " delete ", " create ", " drop ", " alter ", " join ")
        padded = f" {lowered} "
        allowed = lowered.startswith(("select", "show", "explain"))
        if not allowed:
            raise ValueError(
                "R2 SQL examples only allow read-only SELECT, SHOW, or EXPLAIN statements"
            )
        if any(token in padded for token in forbidden):
            raise ValueError(
                "R2 SQL is read-only and single-table; mutating statements and JOINs are "
                "unsupported"
            )
        if lowered.startswith("select") and " limit " not in padded:
            statement = f"{statement} LIMIT 100"
        return statement


@dataclass(frozen=True)
class R2SqlResult:
    sql: str
    data: dict[str, Any]


class R2SqlClient(RestClient[Any]):
    token: str

    def __init__(self, *, account_id: str, bucket_name: str, token: str):
        base_url = (
            "https://api.sql.cloudflarestorage.com/api/v1/accounts/"
            f"{account_id}/r2-sql/query/{bucket_name}"
        )
        super().__init__(raw=None, base_url=base_url)
        object.__setattr__(self, "token", token)

    async def query(self, query: R2SqlQuery) -> R2SqlResult:
        if js is None:
            raise RuntimeError("R2SqlClient requires the Workers runtime js module")
        sql = query.safe_sql()
        response = await js.fetch(
            self.base_url,
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.token}",
                    "content-type": "application/json",
                },
                "body": json.dumps({"query": sql}),
            }),
        )
        raw_data = to_py(await response.json())
        data = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
        return R2SqlResult(sql=sql, data=data)

    async def explain(self, query: R2SqlQuery) -> R2SqlResult:
        return await self.query(R2SqlQuery(f"EXPLAIN {query.safe_sql()}"))


class DemoR2SqlClient:
    async def query(self, query: R2SqlQuery) -> R2SqlResult:
        sql = query.safe_sql()
        return R2SqlResult(sql=sql, data={"rows": [{"bucket": "demo", "objects": 3}]})

    async def explain(self, query: R2SqlQuery) -> R2SqlResult:
        sql = f"EXPLAIN {query.safe_sql()}"
        return R2SqlResult(sql=sql, data={"plan": "single-table scan with LIMIT"})


__all__ = ["DemoR2SqlClient", "R2SqlClient", "R2SqlQuery", "R2SqlResult"]
