from __future__ import annotations

import json
from dataclasses import dataclass
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


class BrowserRendering:
    def __init__(self, account_id: str, token: str):
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering"
        self.token = token

    async def screenshot(self, request: ScreenshotRequest) -> Any:
        return await js.fetch(
            f"{self.base_url}/screenshot",
            to_js({
                "method": "POST",
                "headers": {
                    "authorization": f"Bearer {self.token}",
                    "content-type": "application/json",
                },
                "body": json.dumps(request.payload()),
            }),
        )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        params = parse_qs(urlparse(str(request.url)).query)
        target = params.get("url", ["https://example.com"])[0]
        renderer = BrowserRendering(str(self.env.ACCOUNT_ID), str(self.env.CF_API_TOKEN))
        rendered = await renderer.screenshot(ScreenshotRequest(url=target))
        return Response(rendered.body, headers={"content-type": "image/png"})
