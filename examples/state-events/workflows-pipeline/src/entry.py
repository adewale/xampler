from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint, WorkflowEntrypoint  # type: ignore[import-not-found]

from xampler.d1 import D1Database
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


async def record_timeline(db: D1Database, instance_id: str) -> None:
    now = datetime.now(UTC).isoformat()
    steps = [
        ("fetch input", "complete", "r2://input", {"records": 3}),
        ("transform", "complete", "batch:1", {"records": 3}),
        ("summarize", "complete", "final", {"summary": "INPUT"}),
    ]
    await db.statement("DELETE FROM workflow_timeline WHERE instance_id = ?").run(instance_id)
    for step, state, checkpoint, details in steps:
        await db.statement(
            """
            INSERT INTO workflow_timeline (
              instance_id, step, state, checkpoint, details, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
        ).run(instance_id, step, state, checkpoint, json.dumps(details), now)


async def timeline(db: D1Database, instance_id: str) -> dict[str, Any]:
    rows = await db.query(
        """
        SELECT step, state, checkpoint, details, created_at
        FROM workflow_timeline
        WHERE instance_id = ?
        ORDER BY id
        """,
        instance_id,
    )
    events = [
        {
            **row,
            "details": json.loads(str(row.get("details") or "{}")),
        }
        for row in rows
    ]
    return {"instance_id": instance_id, "events": events, "count": len(events)}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = urlparse(str(request.url))
        db = D1Database(self.env.DB)

        if url.path == "/demo/start":
            started = await DemoWorkflowService().start()
            await record_timeline(db, started.instance_id)
            return Response.json(jsonable(started))

        if url.path.startswith("/timeline/"):
            instance_id = url.path.removeprefix("/timeline/")
            return Response.json(await timeline(db, instance_id))

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
