from __future__ import annotations

from typing import Any

from workers import Response, WorkerEntrypoint

from xampler.experimental.htmlrewriter import OpenGraphPage, OpenGraphRewriter


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        page = OpenGraphPage("Python Workers", "HTML rewritten at the edge")
        html = "<html><head><title>Xampler</title></head><body>Hello</body></html>"
        rewritten = OpenGraphRewriter(page).transform(html)
        return Response(rewritten, headers={"content-type": "text/html; charset=utf-8"})
