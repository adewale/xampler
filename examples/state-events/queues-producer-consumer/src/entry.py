from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js, to_py
from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class QueueJob:
    kind: str
    payload: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class QueueSendOptions:
    delay_seconds: int | None = None

    def as_options(self) -> dict[str, Any] | None:
        if self.delay_seconds is None:
            return None
        return {"delaySeconds": self.delay_seconds}


@dataclass(frozen=True)
class QueueBatchResult:
    processed: int
    retried: int
    dead_lettered: int = 0


class QueueMessage:
    """Python handle around one Queue message.

    Queue handlers should acknowledge or retry each message independently. The
    handle keeps that platform rule visible while converting bodies to Python
    values at the boundary.
    """

    def __init__(self, raw: Any):
        self.raw = raw
        self.body = to_py(raw.body)

    def ack(self) -> None:
        self.raw.ack()

    def retry(self, *, delay_seconds: int) -> None:
        self.raw.retry(to_js({"delaySeconds": delay_seconds}))


class QueueService:
    """Pythonic wrapper for a Queue producer binding."""

    def __init__(self, raw: Any):
        self.raw = raw

    async def send(self, job: QueueJob, options: QueueSendOptions | None = None) -> None:
        body = asdict(job)
        raw_options = (options or QueueSendOptions()).as_options()
        if raw_options:
            await self.raw.send(to_js(body), to_js(raw_options))
        else:
            await self.raw.send(to_js(body))

    async def send_json(self, job: QueueJob, *, delay_seconds: int | None = None) -> None:
        await self.send(job, QueueSendOptions(delay_seconds=delay_seconds))

    async def send_many(self, jobs: list[QueueJob]) -> None:
        await self.raw.sendBatch(to_js([{"body": asdict(job)} for job in jobs]))


class QueueConsumer:
    """Consumes one batch; every message is explicitly acked or retried."""

    def __init__(self, tracker: QueueTrackerRef | None = None, *, is_dead_letter: bool = False):
        self.tracker = tracker
        self.is_dead_letter = is_dead_letter

    async def process_batch(self, batch: Any) -> QueueBatchResult:
        processed = 0
        retried = 0
        dead_lettered = 0
        for raw_message in batch.messages:
            message = QueueMessage(raw_message)
            try:
                if self.is_dead_letter:
                    message.ack()
                    dead_lettered += 1
                    if self.tracker is not None:
                        await self.tracker.record("dead_lettered", message.body)
                    continue
                await self.handle(message.body)
                message.ack()
                processed += 1
                if self.tracker is not None:
                    await self.tracker.record("processed", message.body)
            except Exception:  # noqa: BLE001 - queue handlers isolate failures per message.
                attempts = int(getattr(raw_message, "attempts", 0))
                if isinstance(message.body, dict) and message.body.get("local_dead_letter_after"):
                    message.ack()
                    dead_lettered += 1
                    continue
                payload = message.body.get("payload", {}) if isinstance(message.body, dict) else {}
                if isinstance(payload, dict) and payload.get("source") == "remote-dlq-verifier":
                    delay = 1
                else:
                    delay = min(30 * (2**attempts), 43_200)
                message.retry(delay_seconds=delay)
                retried += 1
                if self.tracker is not None:
                    await self.tracker.record(
                        "retried", {"body": message.body, "attempts": attempts}
                    )
        return QueueBatchResult(processed=processed, retried=retried, dead_lettered=dead_lettered)

    async def handle(self, body: Any) -> None:
        if isinstance(body, dict) and body.get("kind") == "fail":
            raise ValueError("deterministic queue failure")
        print(f"processed queue message: {body}")


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


class QueueTrackerRef:
    def __init__(self, raw_stub: Any):
        self.raw = raw_stub

    async def reset(self) -> dict[str, Any]:
        response = await self.raw.fetch("https://queue-tracker.local/reset")
        return to_py(await response.json())

    async def snapshot(self) -> dict[str, Any]:
        response = await self.raw.fetch("https://queue-tracker.local/status")
        return to_py(await response.json())

    async def record(self, kind: str, body: Any) -> None:
        request = js.Request.new(
            "https://queue-tracker.local/record",
            to_js({
                "method": "POST",
                "headers": {"content-type": "application/json"},
                "body": json.dumps({"kind": kind, "body": body}),
            }),
        )
        await self.raw.fetch(request)


class QueueTrackerNamespace:
    def __init__(self, raw: Any):
        self.raw = raw

    def global_tracker(self) -> QueueTrackerRef:
        return QueueTrackerRef(self.raw.get(self.raw.idFromName("global")))


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
