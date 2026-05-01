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


class R2SqlClient:
    def __init__(self, *, account_id: str, token: str):
        self.url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/sql/query"
        self.token = token

    async def query(self, query: R2SqlQuery) -> dict[str, Any]:
        response = await js.fetch(
            self.url,
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.token}",
                    "content-type": "application/json",
                },
                "body": json.dumps({"sql": query.sql}),
            }),
        )
        return to_py(await response.json())


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        body = to_py(await request.json()) if request.method == "POST" else {}
        sql = body.get("sql", "SHOW DATABASES")
        client = R2SqlClient(account_id=str(self.env.ACCOUNT_ID), token=str(self.env.CF_API_TOKEN))
        return Response.json(await client.query(R2SqlQuery(sql)))
