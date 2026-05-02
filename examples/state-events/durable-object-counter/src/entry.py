from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]


class Counter(DurableObject):
    """A named Durable Object that owns one counter value.

    Literate note: every counter name maps to one Durable Object instance. That
    makes increments strongly ordered for that name without a separate database.
    """

    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        value = int((await self.ctx.storage.get("value")) or 0)

        if path.endswith("/increment"):
            value += 1
            await self.ctx.storage.put("value", value)
            return Response(str(value))

        if path.endswith("/reset"):
            await self.ctx.storage.put("value", 0)
            return Response("0")

        return Response(str(value))


class CounterRef:
    """Typed handle for one named Durable Object counter stub."""

    def __init__(self, name: str, raw_stub: Any):
        self.name = name
        self.raw = raw_stub

    async def value(self) -> int:
        response = await self.raw.fetch(f"https://counter.local/{self.name}")
        return int(await response.text())

    async def increment(self) -> int:
        response = await self.raw.fetch(f"https://counter.local/{self.name}/increment")
        return int(await response.text())

    async def reset(self) -> int:
        response = await self.raw.fetch(f"https://counter.local/{self.name}/reset")
        return int(await response.text())

    async def fetch(self, request: Any) -> Response:
        return await self.raw.fetch(request)


class CounterNamespace:
    """Pythonic wrapper around the Durable Object namespace binding."""

    def __init__(self, raw: Any):
        self.raw = raw

    def named(self, name: str) -> CounterRef:
        return CounterRef(name, self.raw.get(self.raw.idFromName(name)))


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = urlparse(str(request.url))
        parts = [part for part in url.path.split("/") if part]
        if not parts:
            return Response(
                "Use /<counter-name>, /<counter-name>/increment, "
                "or /<counter-name>/reset"
            )

        stub = CounterNamespace(self.env.COUNTERS).named(parts[0])
        return await stub.fetch(request)
