from dataclasses import dataclass

from workers import Response, WorkerEntrypoint


@dataclass(frozen=True)
class OpenGraphPage:
    title: str
    description: str

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        page = OpenGraphPage("Python Workers", "HTML rewritten at the edge")
        html = (
            "<html><head>"
            f"<meta property='og:title' content='{page.title}'>"
            f"</head><body>{page.description}</body></html>"
        )
        return Response(html, headers={"content-type": "text/html"})
