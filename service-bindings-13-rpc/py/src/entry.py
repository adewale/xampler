from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def highlight_code(self, code: str) -> str:
        return highlight(code, PythonLexer(), HtmlFormatter())

    async def fetch(self, request):
        html = await self.highlight_code("print('service binding rpc')")
        return Response(html, headers={"content-type": "text/html; charset=utf-8"})
