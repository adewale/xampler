from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from cfboundary.ffi import to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class QueueJob:
    kind: str
    payload: dict[str, Any]


class QueueService:
    """Pythonic wrapper for a Queue producer binding."""

    def __init__(self, raw: Any):
        self.raw = raw

    async def send_json(self, job: QueueJob, *, delay_seconds: int | None = None) -> None:
        options = {"delaySeconds": delay_seconds} if delay_seconds is not None else None
        body = asdict(job)
        if options:
            await self.raw.send(to_js(body), to_js(options))
        else:
            await self.raw.send(to_js(body))

    async def send_many(self, jobs: list[QueueJob]) -> None:
        await self.raw.sendBatch(to_js([{"body": asdict(job)} for job in jobs]))


class QueueConsumer:
    """Consumes one batch; every message is explicitly acked or retried."""

    async def process_batch(self, batch: Any) -> list[dict[str, Any]]:
        processed: list[dict[str, Any]] = []
        for message in batch.messages:
            try:
                body = to_py(message.body)
                processed.append(body)
                message.ack()
            except Exception:  # noqa: BLE001 - queue handlers must isolate failures per message.
                delay = min(30 * (2 ** int(getattr(message, "attempts", 0))), 43_200)
                message.retry(to_js({"delaySeconds": delay}))
        return processed


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        if request.method == "POST":
            data = to_py(await request.json())
            job = QueueJob(
                kind=str(data.get("kind", "demo")),
                payload=dict(data.get("payload", {})),
            )
            await QueueService(self.env.JOBS).send_json(job)
            return Response.json({"queued": asdict(job)}, status=202)
        return Response("POST JSON to /jobs to enqueue a message.\n")

    async def queue(self, batch: Any, env: Any, ctx: Any) -> None:
        await QueueConsumer().process_batch(batch)
