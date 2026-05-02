from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


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
                "R2 SQL is read-only and single-table; "
                "mutating statements and JOINs are unsupported"
            )
        if lowered.startswith("select") and " limit " not in padded:
            statement = f"{statement} LIMIT 100"
        return statement


@dataclass(frozen=True)
class R2SqlResult:
    sql: str
    data: dict[str, Any]


class R2SqlClient:
    def __init__(self, *, account_id: str, bucket_name: str, token: str):
        self.url = (
            "https://api.sql.cloudflarestorage.com/api/v1/accounts/"
            f"{account_id}/r2-sql/query/{bucket_name}"
        )
        self.token = token

    async def query(self, query: R2SqlQuery) -> R2SqlResult:
        sql = query.safe_sql()
        response = await js.fetch(
            self.url,
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.token}",
                    "content-type": "application/json",
                },
                "body": json.dumps({"query": sql}),
            }),
        )
        return R2SqlResult(sql=sql, data=to_py(await response.json()))

    async def explain(self, query: R2SqlQuery) -> R2SqlResult:
        return await self.query(R2SqlQuery(f"EXPLAIN {query.safe_sql()}"))


class DemoR2SqlClient:
    async def query(self, query: R2SqlQuery) -> R2SqlResult:
        sql = query.safe_sql()
        return R2SqlResult(sql=sql, data={"rows": [{"bucket": "demo", "objects": 3}]})

    async def explain(self, query: R2SqlQuery) -> R2SqlResult:
        sql = f"EXPLAIN {query.safe_sql()}"
        return R2SqlResult(sql=sql, data={"plan": "single-table scan with LIMIT"})


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = str(request.url)
        if request.method == "GET" and url.endswith("/"):
            return Response("POST SQL to /demo locally or / with real R2 SQL credentials.\n")

        body = to_py(await request.json()) if request.method == "POST" else {}
        query = R2SqlQuery(str(body.get("sql", "SHOW DATABASES")))

        if url.endswith("/demo"):
            return Response.json((await DemoR2SqlClient().query(query)).__dict__)
        if url.endswith("/demo/explain"):
            return Response.json((await DemoR2SqlClient().explain(query)).__dict__)

        client = R2SqlClient(
            account_id=str(self.env.ACCOUNT_ID),
            bucket_name=str(self.env.BUCKET_NAME),
            token=str(self.env.CF_API_TOKEN),
        )
        try:
            result = await client.query(query)
        except ValueError as exc:
            return Response.json({"error": str(exc)}, status=400)
        return Response.json(result.__dict__)
