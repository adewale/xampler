from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from workers import WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def highlight_code(self, code: str) -> str:
        return highlight(code, PythonLexer(), HtmlFormatter())
