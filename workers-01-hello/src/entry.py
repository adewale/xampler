from __future__ import annotations

from typing import Any

from cfboundary.ffi import to_js

try:
    import js  # type: ignore[import-not-found]
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:
    js = None  # type: ignore[assignment]

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


class Default(WorkerEntrypoint):
    """The smallest useful Python Worker.

    Literate note: all examples keep the Worker entrypoint thin. Real work should
    move into small Python service objects so it can be tested outside Workers.
    """

    async def fetch(self, request: Any) -> Any:
        return response("Hello from a Pythonic Worker")


def response(body: str, *, status: int = 200) -> Any:
    """Create a Worker Response while keeping JS conversion in one place."""

    if js is None:
        return {"body": body, "status": status}
    return js.Response.new(body, to_js({"status": status}))
