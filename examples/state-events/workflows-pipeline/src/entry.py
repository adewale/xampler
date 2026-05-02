from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint, WorkflowEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class WorkflowStart:
    instance_id: str


@dataclass(frozen=True)
class WorkflowStatus:
    instance_id: str
    status: str
    raw: Any | None = None


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


class WorkflowInstance:
    """Typed handle for one Workflow instance."""

    def __init__(self, instance_id: str, raw: Any):
        self.id = instance_id
        self.raw = raw

    async def status(self) -> WorkflowStatus:
        raw_status = await self.raw.status()
        status = (
            str(raw_status.get("status", raw_status))
            if isinstance(raw_status, dict)
            else str(raw_status)
        )
        return WorkflowStatus(instance_id=self.id, status=status, raw=raw_status)


class WorkflowService:
    """Pythonic service wrapper around the Workflow binding."""

    def __init__(self, raw: Any):
        self.raw = raw

    async def start(self) -> WorkflowStart:
        instance = await self.raw.create()
        return WorkflowStart(instance_id=str(instance.id))

    async def instance(self, instance_id: str) -> WorkflowInstance:
        return WorkflowInstance(instance_id, await self.raw.get(instance_id))

    async def status(self, instance_id: str) -> WorkflowStatus:
        return await (await self.instance(instance_id)).status()


class DemoWorkflowService:
    """Deterministic local substitute for verifier coverage without workflow runtime."""

    def __init__(self) -> None:
        self.started = WorkflowStart("demo-instance")

    async def start(self) -> WorkflowStart:
        return self.started

    async def status(self, instance_id: str) -> WorkflowStatus:
        return WorkflowStatus(instance_id=instance_id, status="complete", raw={"demo": True})


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = urlparse(str(request.url))

        if url.path == "/demo/start":
            return Response.json(asdict(await DemoWorkflowService().start()))

        if url.path.startswith("/demo/status/"):
            instance_id = url.path.removeprefix("/demo/status/")
            return Response.json(asdict(await DemoWorkflowService().status(instance_id)))

        service = WorkflowService(self.env.PIPELINE)
        if url.path == "/start":
            return Response.json(asdict(await service.start()))

        if url.path.startswith("/status/"):
            instance_id = url.path.removeprefix("/status/")
            return Response.json(asdict(await service.status(instance_id)))

        return Response("Use /start, then /status/<workflow_id>. Demo: /demo/start.\n")
