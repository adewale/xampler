from __future__ import annotations

from dataclasses import asdict
from typing import Any
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.browser_rendering import BrowserRendering, DemoBrowserRendering, ScreenshotRequest


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        parsed = urlparse(str(request.url))
        params = parse_qs(parsed.query)
        target = params.get("url", ["https://example.com"])[0]
        if parsed.path == "/demo":
            result = await DemoBrowserRendering().screenshot(ScreenshotRequest(url=target))
            return Response.json(asdict(result))
        if parsed.path == "/demo/content":
            return Response(
                "<html><title>Example Domain</title></html>",
                headers={"content-type": "text/html"},
            )
        if parsed.path == "/demo/pdf":
            return Response("%PDF-1.4 demo", headers={"content-type": "application/pdf"})
        if parsed.path == "/demo/scrape":
            return Response.json({"url": target, "title": "Example Domain", "source": "demo"})

        render_request = ScreenshotRequest(url=target)
        renderer = BrowserRendering(str(self.env.ACCOUNT_ID), str(self.env.CF_API_TOKEN))
        if parsed.path == "/content":
            rendered = await renderer.content(render_request)
            return Response(rendered.body, headers={"content-type": "text/html; charset=utf-8"})
        if parsed.path == "/pdf":
            rendered = await renderer.pdf(render_request)
            return Response(rendered.body, headers={"content-type": "application/pdf"})
        if parsed.path == "/scrape":
            rendered = await renderer.scrape(render_request)
            return Response(rendered.body, headers={"content-type": "application/json"})
        rendered = await renderer.screenshot(render_request)
        return Response(rendered.body, headers={"content-type": "image/png"})
