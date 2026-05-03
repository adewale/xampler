from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.durable_objects import DurableObjectNamespace, DurableObjectRef


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


class CounterRef(DurableObjectRef):
    """Typed handle for one named Durable Object counter stub."""

    async def value(self) -> int:
        return int(await self.text("/"))

    async def increment(self) -> int:
        return int(await self.text("/increment"))

    async def reset(self) -> int:
        return int(await self.text("/reset"))


class CounterNamespace(DurableObjectNamespace[CounterRef]):
    """Pythonic wrapper around the Durable Object namespace binding."""

    def __init__(self, raw: Any):
        super().__init__(raw, ref_type=CounterRef)


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
