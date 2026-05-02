from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from workers import Response, WorkerEntrypoint


@dataclass(frozen=True)
class OpenGraphPage:
    title: str
    description: str
    image_url: str | None = None


class OpenGraphRewriter:
    """Small Python wrapper for an edge HTML metadata transformation.

    Python Workers do not currently expose a polished Python-native HTMLRewriter
    class, so this example keeps the transformation explicit, typed, and safe:
    user-controlled values are escaped, the operation is isolated in a service
    object, and the Worker route remains thin. When the platform surface grows,
    this class is the seam where a direct `.raw` HTMLRewriter can be introduced.
    """

    def __init__(self, page: OpenGraphPage):
        self.page = page

    def transform(self, html: str) -> str:
        tags = [
            self._meta("og:title", self.page.title),
            self._meta("og:description", self.page.description),
        ]
        if self.page.image_url:
            tags.append(self._meta("og:image", self.page.image_url))
        return html.replace("</head>", "".join(tags) + "</head>")

    def _meta(self, property_name: str, content: str) -> str:
        return (
            f'<meta property="{escape(property_name)}" '
            f'content="{escape(content, quote=True)}">'
        )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        page = OpenGraphPage("Python Workers", "HTML rewritten at the edge")
        html = "<html><head><title>Xampler</title></head><body>Hello</body></html>"
        rewritten = OpenGraphRewriter(page).transform(html)
        return Response(rewritten, headers={"content-type": "text/html; charset=utf-8"})
