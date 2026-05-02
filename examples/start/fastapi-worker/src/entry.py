from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from workers import WorkerEntrypoint  # type: ignore[import-not-found]

# Literate note: FastAPI remains the Python application object. The only
# Workers-specific code is the tiny adapter in Default.fetch(). That is the
# important pattern: keep framework code ordinary and isolate the platform edge.
app = FastAPI(title="Xampler FastAPI Worker")


@app.get("/")
async def home() -> dict[str, str]:
    """A normal FastAPI route running at the edge."""

    return {"message": "Hello from FastAPI on Workers", "next": "/items/python"}


@app.get("/items/{item_id}")
async def get_item(item_id: str) -> dict[str, str]:
    """Path parameters work the same way they do in regular FastAPI apps."""

    return {"item_id": item_id}


@app.get("/env")
async def get_env(request: Request) -> dict[str, str]:
    """FastAPI can still access the Workers environment through ASGI scope."""

    env = request.scope["env"]
    return {"message": str(getattr(env, "MESSAGE", "set MESSAGE in wrangler.jsonc"))}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        # Import inside the handler to match the official Python Workers pattern.
        # `request.js_object` passes the native JS Request to the ASGI bridge.
        import asgi  # type: ignore[import-not-found]

        return await asgi.fetch(app, request.js_object, self.env)
