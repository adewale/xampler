from __future__ import annotations

from typing import Any

from cfboundary.ffi import to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.r2_sql import DemoR2SqlClient, R2SqlClient, R2SqlQuery


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
