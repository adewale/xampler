from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse

from cfboundary.ffi import to_py
from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.queues import QueueConsumer, QueueJob, QueueService, QueueTrackerNamespace


class QueueTracker(DurableObject):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path.endswith("/reset"):
            await self.ctx.storage.put("processed", 0)
            await self.ctx.storage.put("retried", 0)
            await self.ctx.storage.put("dead_lettered", 0)
            await self.ctx.storage.put("events", "[]")
            return Response.json(await self.snapshot())
        if path.endswith("/record"):
            event = json.loads(str(await request.text()))
            kind = str(event.get("kind", "processed"))
            current = int((await self.ctx.storage.get(kind)) or 0)
            await self.ctx.storage.put(kind, current + 1)
            events = json.loads(str((await self.ctx.storage.get("events")) or "[]"))
            events.append(event)
            await self.ctx.storage.put("events", json.dumps(events[-20:]))
            return Response.json(await self.snapshot())
        return Response.json(await self.snapshot())

    async def snapshot(self) -> dict[str, Any]:
        return {
            "processed": int((await self.ctx.storage.get("processed")) or 0),
            "retried": int((await self.ctx.storage.get("retried")) or 0),
            "dead_lettered": int((await self.ctx.storage.get("dead_lettered")) or 0),
            "events": json.loads(str((await self.ctx.storage.get("events")) or "[]")),
        }


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if request.method == "POST" and path == "/jobs":
            data = to_py(await request.json())
            job = QueueJob(
                kind=str(data.get("kind", "demo")),
                payload=dict(data.get("payload", {})),
            )
            await QueueService(self.env.JOBS).send(job)
            return Response.json({"queued": asdict(job)}, status=202)
        if request.method == "POST" and path == "/dev/process-sample":
            result = await QueueConsumer().process_batch(
                FakeQueueBatch([asdict(QueueJob("demo", {"source": "verifier"}))])
            )
            return Response.json(asdict(result))
        if request.method == "POST" and path == "/dev/process-failing":
            result = await QueueConsumer().process_batch(
                FakeQueueBatch(
                    [
                        {
                            **asdict(QueueJob("fail", {"source": "verifier"})),
                            "local_dead_letter_after": True,
                        }
                    ],
                    attempts=3,
                )
            )
            return Response.json(asdict(result))
        if request.method == "POST" and path == "/dev/remote-reset":
            tracker = QueueTrackerNamespace(self.env.TRACKER).global_tracker()
            return Response.json(await tracker.reset())
        if path == "/dev/remote-status":
            return Response.json(
                await QueueTrackerNamespace(self.env.TRACKER).global_tracker().snapshot()
            )
        return Response("POST JSON to /jobs to enqueue a message.\n")

    async def queue(self, batch: Any, env: Any, ctx: Any) -> None:
        bindings = env or self.env
        tracker = QueueTrackerNamespace(bindings.TRACKER).global_tracker()
        queue_name = str(getattr(batch, "queue", ""))
        is_dead_letter = queue_name == "xampler-jobs-dlq"
        await QueueConsumer(tracker, is_dead_letter=is_dead_letter).process_batch(batch)


class FakeQueueMessage:
    """Local verifier stand-in with the same ack/retry methods as Queue messages."""

    def __init__(self, body: dict[str, Any]):
        self.body = body
        self.attempts = 0
        self.acked = False
        self.retried = False

    def ack(self) -> None:
        self.acked = True

    def retry(self, options: Any) -> None:
        self.retried = True


class FakeQueueBatch:
    def __init__(self, bodies: list[dict[str, Any]], *, attempts: int = 0):
        self.messages = [FakeQueueMessage(body) for body in bodies]
        for message in self.messages:
            message.attempts = attempts
