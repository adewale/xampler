from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint, WorkflowEntrypoint  # type: ignore[import-not-found]


class Pipeline(WorkflowEntrypoint):
    """A small DAG workflow.

    Literate note: Workflows are for durable multi-step work. Each `step.do()` is
    named so Cloudflare can track/retry it. The Python code reads like ordinary
    async orchestration, but the platform gives it durable execution semantics.
    """

    async def run(self, event: Any, step: Any) -> None:
        @step.do("fetch input")
        async def fetch_input() -> str:
            await asyncio.sleep(0)
            return "input"

        @step.do("transform", depends=[fetch_input])
        async def transform(value: str = "input") -> str:
            return value.upper()

        @step.do("summarize", depends=[transform])
        async def summarize(value: str = "INPUT") -> None:
            print(f"Workflow complete: {value}")

        await summarize()


class WorkflowService:
    """Pythonic service wrapper around the Workflow binding."""

    def __init__(self, raw: Any):
        self.raw = raw

    async def start(self) -> str:
        instance = await self.raw.create()
        return str(instance.id)

    async def status(self, instance_id: str) -> Any:
        instance = await self.raw.get(instance_id)
        return await instance.status()


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        service = WorkflowService(self.env.PIPELINE)
        url = urlparse(str(request.url))

        if url.path == "/start":
            instance_id = await service.start()
            return Response(f"Started workflow {instance_id}\n")

        if url.path.startswith("/status/"):
            instance_id = url.path.removeprefix("/status/")
            return Response.json(await service.status(instance_id))

        return Response("Use /start, then /status/<workflow_id>.\n")
