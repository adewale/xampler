from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

ImageType = Literal["png", "jpeg"]


@dataclass(frozen=True, kw_only=True)
class ScreenshotRequest:
    url: str
    full_page: bool = True
    image_type: ImageType = "png"

    def payload(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "screenshotOptions": {"fullPage": self.full_page, "type": self.image_type},
        }


@dataclass(frozen=True)
class ScreenshotResult:
    url: str
    image_type: ImageType
    bytes: int
    source: str


class BrowserRendering:
    def __init__(self, account_id: str, token: str):
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering"
        self.token = token

    async def render(self, endpoint: str, request: ScreenshotRequest) -> Any:
        return await js.fetch(
            f"{self.base_url}/{endpoint}",
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.token}",
                    "content-type": "application/json",
                },
                "body": json.dumps(request.payload()),
            }),
        )

    async def screenshot(self, request: ScreenshotRequest) -> Any:
        return await self.render("screenshot", request)

    async def pdf(self, request: ScreenshotRequest) -> Any:
        return await self.render("pdf", request)

    async def content(self, request: ScreenshotRequest) -> Any:
        return await self.render("content", request)

    async def scrape(self, request: ScreenshotRequest) -> Any:
        return await self.render("scrape", request)


class DemoBrowserRendering:
    raw = None

    async def screenshot(self, request: ScreenshotRequest) -> ScreenshotResult:
        return ScreenshotResult(
            url=request.url,
            image_type=request.image_type,
            bytes=67,
            source="demo-browser-rendering",
        )


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
