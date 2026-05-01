from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


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

    async def process_batch(self, batch: Any) -> QueueBatchResult:
        processed = 0
        retried = 0
        for raw_message in batch.messages:
            message = QueueMessage(raw_message)
            try:
                await self.handle(message.body)
                message.ack()
                processed += 1
            except Exception:  # noqa: BLE001 - queue handlers isolate failures per message.
                delay = min(30 * (2 ** int(getattr(raw_message, "attempts", 0))), 43_200)
                message.retry(delay_seconds=delay)
                retried += 1
        return QueueBatchResult(processed=processed, retried=retried)

    async def handle(self, body: Any) -> None:
        print(f"processed queue message: {body}")


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
        return Response("POST JSON to /jobs to enqueue a message.\n")

    async def queue(self, batch: Any, env: Any, ctx: Any) -> None:
        await QueueConsumer().process_batch(batch)


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
    def __init__(self, bodies: list[dict[str, Any]]):
        self.messages = [FakeQueueMessage(body) for body in bodies]
