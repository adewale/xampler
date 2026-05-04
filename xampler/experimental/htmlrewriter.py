from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class OpenGraphPage:
    title: str
    description: str
    image_url: str | None = None


class OpenGraphRewriter:
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
