from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint, WorkflowEntrypoint  # type: ignore[import-not-found]

from xampler.response import jsonable
from xampler.workflows import DemoWorkflowService, WorkflowService


class Pipeline(WorkflowEntrypoint):
    """A small DAG workflow with named durable steps."""

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


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = urlparse(str(request.url))

        if url.path == "/demo/start":
            return Response.json(jsonable(await DemoWorkflowService().start()))

        if url.path.startswith("/demo/status/"):
            instance_id = url.path.removeprefix("/demo/status/")
            return Response.json(jsonable(await DemoWorkflowService().status(instance_id)))

        service = WorkflowService(self.env.PIPELINE)
        if url.path == "/start":
            return Response.json(jsonable(await service.start()))

        if url.path.startswith("/status/"):
            instance_id = url.path.removeprefix("/status/")
            return Response.json(jsonable(await service.status(instance_id)))

        return Response("Use /start, then /status/<workflow_id>. Demo: /demo/start.\n")
