from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from xampler.experimental.htmlrewriter import OpenGraphPage, OpenGraphRewriter

FIXTURE_HTML = """<html><head>
<title>Xampler Fixture</title>
<meta property="og:title" content="Fixture OG Title">
<meta property="og:description" content="Fixture description">
<link rel="canonical" href="https://example.com/fixture">
</head><body><h1>Hello</h1></body></html>"""


@dataclass(frozen=True)
class ExtractedMetadata:
    title: str | None
    og_title: str | None
    og_description: str | None
    canonical_url: str | None


def attr(html_text: str, pattern: str) -> str | None:
    match = re.search(pattern, html_text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def extract_metadata(html_text: str) -> ExtractedMetadata:
    return ExtractedMetadata(
        title=attr(html_text, r"<title>(.*?)</title>"),
        og_title=attr(html_text, r'<meta property="og:title" content="([^"]+)">'),
        og_description=attr(html_text, r'<meta property="og:description" content="([^"]+)">'),
        canonical_url=attr(html_text, r'<link rel="canonical" href="([^"]+)">'),
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/fixture":
            return Response(FIXTURE_HTML, headers={"content-type": "text/html; charset=utf-8"})
        if path == "/extract":
            return Response.json(asdict(extract_metadata(FIXTURE_HTML)))
        page = OpenGraphPage("Python Workers", "HTML rewritten at the edge")
        html = "<html><head><title>Xampler</title></head><body>Hello</body></html>"
        rewritten = OpenGraphRewriter(page).transform(html)
        return Response(rewritten, headers={"content-type": "text/html; charset=utf-8"})
