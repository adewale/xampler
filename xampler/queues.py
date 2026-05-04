from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol, cast

from cfboundary.ffi import to_js, to_py

from xampler.cloudflare import CloudflareService


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
    """Python handle around one Queue message."""

    def __init__(self, raw: Any):
        self.raw = raw
        self.body: Any = to_py(raw.body)

    def ack(self) -> None:
        self.raw.ack()

    def retry(self, *, delay_seconds: int) -> None:
        self.raw.retry(to_js({"delaySeconds": delay_seconds}))


class QueueService(CloudflareService[Any]):
    """Pythonic wrapper for a Queue producer binding."""

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


class QueueEventRecorder(Protocol):
    """Capability for queue observability sinks used by consumers.

    The recorder may be backed by a Durable Object, D1, logs, or an in-memory
    test object. It is not a Queues product API.
    """

    async def record(self, kind: str, body: Any) -> None: ...


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return cast(dict[str, Any], value) if isinstance(value, dict) else None


class QueueConsumer:
    """Consumes one batch; every message is explicitly acked or retried."""

    def __init__(self, recorder: QueueEventRecorder | None = None, *, is_dead_letter: bool = False):
        self.recorder = recorder
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
                    if self.recorder is not None:
                        await self.recorder.record("dead_lettered", message.body)
                    continue
                await self.handle(message.body)
                message.ack()
                processed += 1
                if self.recorder is not None:
                    await self.recorder.record("processed", message.body)
            except Exception:  # noqa: BLE001 - queue handlers isolate failures per message.
                attempts = int(getattr(raw_message, "attempts", 0))
                body_dict = _dict_or_none(message.body)
                if body_dict is not None and body_dict.get("local_dead_letter_after"):
                    message.ack()
                    dead_lettered += 1
                    continue
                payload: Any = body_dict.get("payload", {}) if body_dict is not None else {}
                delay = (
                    1
                    if (payload_dict := _dict_or_none(payload)) is not None
                    and payload_dict.get("source") == "remote-dlq-verifier"
                    else min(30 * (2**attempts), 43_200)
                )
                message.retry(delay_seconds=delay)
                retried += 1
                if self.recorder is not None:
                    await self.recorder.record(
                        "retried", {"body": message.body, "attempts": attempts}
                    )
        return QueueBatchResult(processed=processed, retried=retried, dead_lettered=dead_lettered)

    async def handle(self, body: Any) -> None:
        body_dict = _dict_or_none(body)
        if body_dict is not None and body_dict.get("kind") == "fail":
            raise ValueError("deterministic queue failure")
        print(f"processed queue message: {body}")


__all__ = [
    "QueueBatchResult",
    "QueueConsumer",
    "QueueEventRecorder",
    "QueueJob",
    "QueueMessage",
    "QueueSendOptions",
    "QueueService",
]
