from __future__ import annotations

import json
import zipfile
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any, Literal, TypeVar
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import is_js_missing, to_js_bytes, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

T = TypeVar("T")
GUTENBERG_KEY = "gutenberg/100/raw/pg100-h.zip"
GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/100/pg100-h.zip"
SAMPLE_TEXT = """The Project Gutenberg eBook of The Complete Works of William Shakespeare
Romeo and Juliet
But soft, what light through yonder window breaks?
Hamlet
To be, or not to be, that is the question.
The Tempest
We are such stuff as dreams are made on.
"""


@dataclass(frozen=True)
class StreamCheckpoint:
    name: str
    offset: int
    records: int
    status: Literal["running", "complete"] = "running"


@dataclass(frozen=True)
class TextRecord:
    line_no: int
    text: str


@dataclass(frozen=True)
class BatchResult:
    batches: int
    records: int
    checkpoint: StreamCheckpoint


@dataclass(frozen=True)
class AgentEvent:
    type: Literal["token", "tool_call", "done"]
    data: dict[str, Any]


class ByteStream:
    def __init__(self, chunks: AsyncIterable[bytes]):
        self.chunks = chunks

    async def iter_bytes(self) -> AsyncIterator[bytes]:
        async for chunk in self.chunks:
            yield chunk

    async def iter_text(self, encoding: str = "utf-8") -> AsyncIterator[str]:
        async for chunk in self.iter_bytes():
            yield chunk.decode(encoding, errors="replace")

    async def iter_lines(self) -> AsyncIterator[str]:
        carry = ""
        async for text in self.iter_text():
            carry += text
            *lines, carry = carry.split("\n")
            for line in lines:
                yield line
        if carry:
            yield carry


class RecordStream[T]:
    def __init__(self, records: AsyncIterable[T]):
        self.records = records

    async def map(self, func: Callable[[T], Any]) -> AsyncIterator[Any]:
        async for record in self.records:
            yield func(record)

    async def tap(self, func: Callable[[T], Awaitable[None]]) -> AsyncIterator[T]:
        async for record in self.records:
            await func(record)
            yield record

    async def batch(self, size: int) -> AsyncIterator[list[T]]:
        batch: list[T] = []
        async for record in self.records:
            batch.append(record)
            if len(batch) >= size:
                yield batch
                batch = []
        if batch:
            yield batch


class JsonlReader:
    def __init__(self, lines: AsyncIterable[str]):
        self.lines = lines

    async def records(self) -> AsyncIterator[dict[str, Any]]:
        async for line in self.lines:
            if line.strip():
                yield json.loads(line)


async def aiter_batches[T](records: AsyncIterable[T], size: int) -> AsyncIterator[list[T]]:
    async for batch in RecordStream(records).batch(size):
        yield batch


async def bytes_from_text(text: str, chunk_size: int = 48) -> AsyncIterator[bytes]:
    data = text.encode()
    for offset in range(0, len(data), chunk_size):
        yield data[offset : offset + chunk_size]


class DemoD1Sink:
    def __init__(self) -> None:
        self.rows: list[TextRecord] = []
        self.checkpoint = StreamCheckpoint("gutenberg-demo", 0, 0)

    async def insert_batch(self, rows: list[TextRecord]) -> None:
        self.rows.extend(rows)
        self.checkpoint = StreamCheckpoint(
            "gutenberg-demo",
            offset=self.checkpoint.offset + len(rows),
            records=len(self.rows),
        )

    async def complete(self) -> StreamCheckpoint:
        self.checkpoint = StreamCheckpoint(
            self.checkpoint.name,
            self.checkpoint.offset,
            self.checkpoint.records,
            "complete",
        )
        return self.checkpoint


class DemoAIService:
    async def stream_text(self, prompt: str) -> AsyncIterator[str]:
        for token in ["summary", ": ", prompt[:24], "..."]:
            yield token


class DemoAgentSession:
    async def stream(self, message: str) -> AsyncIterator[AgentEvent]:
        yield AgentEvent("tool_call", {"name": "gutenberg.search", "query": message})
        yield AgentEvent("token", {"text": "Found Shakespeare lines."})
        yield AgentEvent("done", {"status": "complete"})


class DemoWebSocketSession:
    async def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        yield {"type": "open"}
        yield {"type": "message", "text": "stream checkpoint advanced"}
        yield {"type": "close"}


async def composed_pipeline() -> dict[str, Any]:
    byte_stream = ByteStream(bytes_from_text(SAMPLE_TEXT))

    async def line_records() -> AsyncIterator[TextRecord]:
        async for idx, line in async_enumerate(byte_stream.iter_lines(), start=1):
            if line.strip():
                yield TextRecord(idx, line)

    sink = DemoD1Sink()
    batches = 0
    async for batch in aiter_batches(line_records(), size=3):
        await sink.insert_batch(batch)
        batches += 1
    checkpoint = await sink.complete()
    return {
        "source": "gutenberg-stream-demo",
        "golden_key": GUTENBERG_KEY,
        "result": asdict(BatchResult(batches, len(sink.rows), checkpoint)),
        "first_rows": [asdict(row) for row in sink.rows[:3]],
    }


async def async_enumerate[T](
    iterable: AsyncIterable[T], start: int = 0
) -> AsyncIterator[tuple[int, T]]:
    index = start
    async for item in iterable:
        yield index, item
        index += 1


async def js_readable_stream_chunks(stream: Any) -> AsyncIterator[bytes]:
    reader = stream.getReader()
    while True:
        result = await reader.read()
        if bool(getattr(result, "done", False)):
            break
        value = getattr(result, "value", None)
        if value is not None:
            yield bytes(to_py(value))


async def ensure_gutenberg_r2_object(bucket: Any) -> bool:
    if not is_js_missing(await bucket.head(GUTENBERG_KEY)):
        return False
    response = await js.fetch(GUTENBERG_URL)
    data = bytes(to_py(await response.arrayBuffer()))
    await bucket.put(GUTENBERG_KEY, to_js_bytes(data))
    return True


async def read_r2_object_body(bucket: Any, key: str) -> tuple[bytes, int]:
    obj = await bucket.get(key)
    if is_js_missing(obj):
        raise ValueError(f"R2 object not found: {key}")
    chunks: list[bytes] = []
    chunk_count = 0
    async for chunk in js_readable_stream_chunks(obj.body):
        chunks.append(chunk)
        chunk_count += 1
    return b"".join(chunks), chunk_count


async def unzip_gutenberg_archive_from_r2(bucket: Any) -> dict[str, Any]:
    seeded = await ensure_gutenberg_r2_object(bucket)
    data, chunk_count = await read_r2_object_body(bucket, GUTENBERG_KEY)
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        html_entries = [info for info in entries if info.filename.endswith((".html", ".htm"))]
        first = html_entries[0] if html_entries else entries[0]
        with archive.open(first) as file:
            sample = file.read(160).decode("utf-8", errors="replace")
    return {
        "source": "r2-object-body",
        "source_url_for_local_seed": GUTENBERG_URL,
        "seeded_from_source_url": seeded,
        "golden_key": GUTENBERG_KEY,
        "zip_bytes": len(data),
        "r2_stream_chunks": chunk_count,
        "r2_streamed_bytes": len(data),
        "entries": len(entries),
        "html_entries": len(html_entries),
        "first_entry": first.filename,
        "sample": sample,
    }


async def stream_events() -> dict[str, Any]:
    ai_chunks = [chunk async for chunk in DemoAIService().stream_text("Shakespeare archive")]
    agent_events = [asdict(event) async for event in DemoAgentSession().stream("Hamlet")]
    websocket_events = [event async for event in DemoWebSocketSession()]
    jsonl = '\n'.join(json.dumps({"n": n}) for n in range(3))
    jsonl_lines = ByteStream(bytes_from_text(jsonl)).iter_lines()
    records = [record async for record in JsonlReader(jsonl_lines).records()]
    return {
        "ai_chunks": ai_chunks,
        "agent_events": agent_events,
        "websocket_events": websocket_events,
        "jsonl_records": records,
    }


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/demo":
            return Response.json(await composed_pipeline())
        if path == "/events":
            return Response.json(await stream_events())
        if path == "/zip-demo":
            return Response.json(await unzip_gutenberg_archive_from_r2(self.env.ARTIFACTS))
        if path == "/golden":
            obj = await self.env.ARTIFACTS.head(GUTENBERG_KEY)
            exists = obj is not None
            return Response.json({
                "key": GUTENBERG_KEY,
                "exists": exists,
                "size": int(getattr(obj, "size", 0) or 0) if exists else 0,
            })
        return Response("Streaming Gutenberg example. Try /demo, /events, or /golden.")
