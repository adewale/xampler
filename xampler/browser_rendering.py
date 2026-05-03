from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from cfboundary.ffi import to_js

from xampler.cloudflare import RestClient

try:
    import js  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    js = None  # type: ignore[assignment]

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


class BrowserRendering(RestClient[Any]):
    token: str

    def __init__(self, account_id: str, token: str):
        super().__init__(
            raw=None,
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering",
        )
        object.__setattr__(self, "token", token)

    async def render(self, endpoint: str, request: ScreenshotRequest) -> Any:
        if js is None:
            raise RuntimeError("BrowserRendering requires the Workers runtime js module")
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


__all__ = [
    "BrowserRendering",
    "DemoBrowserRendering",
    "ImageType",
    "ScreenshotRequest",
    "ScreenshotResult",
]
