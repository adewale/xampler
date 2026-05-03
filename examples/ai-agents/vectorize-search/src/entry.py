from __future__ import annotations

from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse

from cfboundary.ffi import to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.vectorize import DemoVectorIndex, Vector, VectorIndex, VectorQuery, unit_vector


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        index = VectorIndex(self.env.INDEX)
        path = urlparse(str(request.url)).path
        if path == "/demo":
            result = await DemoVectorIndex().search(unit_vector(0), top_k=1)
            return Response.json(asdict(result))
        if path == "/describe":
            return Response.json(await index.describe())
        if request.method == "POST" and path == "/upsert":
            data = to_py(await request.json())
            vector = Vector(**data)
            return Response.json(await index.upsert([vector]))
        if request.method == "POST" and path == "/query":
            data = to_py(await request.json())
            result = await index.query(VectorQuery(**data))
            return Response.json(asdict(result))
        return Response("Use /describe, POST /upsert, or POST /query.\n")
