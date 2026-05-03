from __future__ import annotations

import html
import json
import re
import zipfile
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import d1_null, is_js_missing, to_js, to_js_bytes, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.cloudflare import CloudflareService
from xampler.response import jsonable
from xampler.status import Progress
from xampler.streaming import (
    AgentEvent,
    ByteStream,
    JsonlReader,
    StreamCheckpoint,
    aiter_batches,
    async_enumerate,
)

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
class TextRecord:
    line_no: int
    text: str


@dataclass(frozen=True)
class BatchResult:
    batches: int
    records: int
    checkpoint: StreamCheckpoint


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


class D1Statement:
    def __init__(self, raw_statement: Any):
        self.raw = raw_statement

    def bind(self, *params: Any) -> D1Statement:
        return D1Statement(self.raw.bind(*[d1_null(param) for param in params]))

    async def run(self, *params: Any) -> Any:
        statement = self.bind(*params) if params else self
        return to_py(await statement.raw.run())

    async def all(self, *params: Any) -> list[dict[str, Any]]:
        statement = self.bind(*params) if params else self
        result = to_py(await statement.raw.all())
        return list(result.get("results", []))

    async def first(self, *params: Any) -> dict[str, Any] | None:
        rows = await self.all(*params)
        return rows[0] if rows else None


class D1Database(CloudflareService[Any]):
    def statement(self, sql: str) -> D1Statement:
        return D1Statement(self.raw.prepare(sql))

    async def execute(self, sql: str) -> None:
        for statement in [part.strip() for part in sql.split(";") if part.strip()]:
            await self.statement(statement).run()

    async def batch_run(self, statements: list[D1Statement]) -> None:
        if statements:
            await self.raw.batch(to_js([statement.raw for statement in statements]))


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


async def extract_gutenberg_html(bucket: Any) -> tuple[str, dict[str, Any]]:
    seeded = await ensure_gutenberg_r2_object(bucket)
    data, chunk_count = await read_r2_object_body(bucket, GUTENBERG_KEY)
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        html_entries = [info for info in entries if info.filename.endswith((".html", ".htm"))]
        first = html_entries[0] if html_entries else entries[0]
        with archive.open(first) as file:
            html_text = file.read().decode("utf-8", errors="replace")
    metadata = {
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
    }
    return html_text, metadata


async def unzip_gutenberg_archive_from_r2(bucket: Any) -> dict[str, Any]:
    html_text, metadata = await extract_gutenberg_html(bucket)
    return {**metadata, "sample": html_text[:160]}


def html_to_text(html_text: str, *, tag_separator: str = " ") -> str:
    body = re.sub(r"(?is)<(script|style).*?</\\1>", tag_separator, html_text)
    body = re.sub(r"(?s)<[^>]+>", tag_separator, body)
    text = html.unescape(body)
    if tag_separator == "\n":
        lines = [re.sub(r"\\s+", " ", line).strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)
    return re.sub(r"\\s+", " ", text).strip()


def html_to_text_chunks(html_text: str, *, chunk_size: int = 1200) -> list[str]:
    text = html_to_text(html_text)
    return [text[offset : offset + chunk_size] for offset in range(0, len(text), chunk_size)]


def html_to_text_lines(html_text: str) -> list[str]:
    return [line for line in html_to_text(html_text, tag_separator="\n").splitlines() if line]


def fts_query(text: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return " ".join(tokens[:8]) or "shakespeare"


async def reset_fts(db: D1Database) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS gutenberg_chunks (
          chunk_no INTEGER PRIMARY KEY,
          text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS gutenberg_fts USING fts5(
          chunk_no UNINDEXED,
          text
        );
        DELETE FROM gutenberg_chunks;
        DELETE FROM gutenberg_fts;
        """
    )


async def ingest_gutenberg_fts(bucket: Any, raw_db: Any) -> dict[str, Any]:
    db = D1Database(raw_db)
    html_text, metadata = await extract_gutenberg_html(bucket)
    chunks = html_to_text_chunks(html_text)
    await reset_fts(db)
    batches = 0
    for offset in range(0, len(chunks), 25):
        statements: list[D1Statement] = []
        for chunk_no, text in enumerate(chunks[offset : offset + 25], start=offset + 1):
            statements.append(
                db.statement("INSERT INTO gutenberg_chunks (chunk_no, text) VALUES (?, ?)").bind(
                    chunk_no, text
                )
            )
            statements.append(
                db.statement("INSERT INTO gutenberg_fts (chunk_no, text) VALUES (?, ?)").bind(
                    chunk_no, text
                )
            )
        await db.batch_run(statements)
        batches += 1
    status = await fts_status(raw_db)
    return {
        **metadata,
        "chunks": len(chunks),
        "batches": batches,
        "source_text_chars": sum(len(chunk) for chunk in chunks),
        "status": status,
        "all_chunks_indexed": status["chunks"] == len(chunks) == status["fts_rows"],
    }


async def fts_status(raw_db: Any) -> dict[str, Any]:
    db = D1Database(raw_db)
    chunks = await db.statement("SELECT COUNT(*) AS count FROM gutenberg_chunks").first()
    fts_rows = await db.statement("SELECT COUNT(*) AS count FROM gutenberg_fts").first()
    return {
        "chunks": int((chunks or {}).get("count", 0)),
        "fts_rows": int((fts_rows or {}).get("count", 0)),
    }


async def search_fts(raw_db: Any, query: str) -> dict[str, Any]:
    db = D1Database(raw_db)
    match = fts_query(query)
    rows = await db.statement(
        """
        SELECT chunk_no, snippet(gutenberg_fts, 1, '<mark>', '</mark>', '…', 18) AS snippet
        FROM gutenberg_fts
        WHERE gutenberg_fts MATCH ?
        ORDER BY rank
        LIMIT 5
        """
    ).all(match)
    return {"query": query, "match": match, "count": len(rows), "results": rows}


async def verify_fts(raw_db: Any) -> dict[str, Any]:
    status = await fts_status(raw_db)
    queries = ["romeo juliet", "to be or not to be", "hamlet", "tempest", "king lear"]
    results = [await search_fts(raw_db, query) for query in queries]
    return {
        "status": status,
        "queries": results,
        "all_chunks_indexed": status["chunks"] > 0 and status["chunks"] == status["fts_rows"],
        "all_queries_return_results": all(result["count"] > 0 for result in results),
    }


async def reset_checkpointed_pipeline(db: D1Database) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS gutenberg_pipeline_lines (
          line_no INTEGER PRIMARY KEY,
          text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stream_checkpoints (
          name TEXT PRIMARY KEY,
          offset INTEGER NOT NULL,
          records INTEGER NOT NULL,
          state TEXT NOT NULL
        );
        DELETE FROM gutenberg_pipeline_lines;
        DELETE FROM stream_checkpoints WHERE name = 'gutenberg-r2-lines';
        """
    )


async def checkpointed_pipeline_status(raw_db: Any) -> dict[str, Any]:
    db = D1Database(raw_db)
    rows = await db.statement("SELECT COUNT(*) AS count FROM gutenberg_pipeline_lines").first()
    checkpoint = await db.statement(
        "SELECT name, offset, records, state FROM stream_checkpoints WHERE name = ?"
    ).first("gutenberg-r2-lines")
    return {"lines": int((rows or {}).get("count", 0)), "checkpoint": checkpoint}


async def ingest_r2_lines_checkpointed(bucket: Any, raw_db: Any) -> dict[str, Any]:
    db = D1Database(raw_db)
    html_text, metadata = await extract_gutenberg_html(bucket)
    lines = html_to_text_lines(html_text)
    await reset_checkpointed_pipeline(db)
    batches = 0
    inserted = 0
    for batch in [lines[offset : offset + 250] for offset in range(0, len(lines), 250)]:
        statements: list[D1Statement] = []
        for text in batch:
            inserted += 1
            statements.append(
                db.statement(
                    "INSERT INTO gutenberg_pipeline_lines (line_no, text) VALUES (?, ?)"
                ).bind(inserted, text)
            )
        progress = Progress(
            inserted, len(lines), "running" if inserted < len(lines) else "complete"
        )
        statements.append(
            db.statement(
                """
                INSERT INTO stream_checkpoints (name, offset, records, state)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                  offset = excluded.offset,
                  records = excluded.records,
                  state = excluded.state
                """
            ).bind("gutenberg-r2-lines", inserted, inserted, progress.state)
        )
        await db.batch_run(statements)
        batches += 1
    status = await checkpointed_pipeline_status(raw_db)
    checkpoint = status["checkpoint"]
    checkpoint_records = (
        cast(dict[str, Any], checkpoint).get("records") if isinstance(checkpoint, dict) else None
    )
    return {
        **metadata,
        "source": "r2-zip-to-checkpointed-d1-lines",
        "batches": batches,
        "lines": len(lines),
        "status": status,
        "all_lines_checkpointed": status["lines"] == len(lines)
        and checkpoint_records == len(lines),
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
            return Response.json(jsonable(await stream_events()))
        if path == "/zip-demo":
            return Response.json(
                jsonable(await unzip_gutenberg_archive_from_r2(self.env.ARTIFACTS))
            )
        if path == "/fts/ingest":
            return Response.json(
                jsonable(await ingest_gutenberg_fts(self.env.ARTIFACTS, self.env.DB))
            )
        if path == "/fts/status":
            return Response.json(jsonable(await fts_status(self.env.DB)))
        if path == "/fts/search":
            query = parse_qs(urlparse(str(request.url)).query).get("q", ["hamlet"])[0]
            return Response.json(jsonable(await search_fts(self.env.DB, query)))
        if path == "/fts/verify":
            return Response.json(jsonable(await verify_fts(self.env.DB)))
        if path == "/pipeline/ingest-r2-lines":
            return Response.json(
                jsonable(await ingest_r2_lines_checkpointed(self.env.ARTIFACTS, self.env.DB))
            )
        if path == "/pipeline/status":
            return Response.json(jsonable(await checkpointed_pipeline_status(self.env.DB)))
        if path == "/golden":
            obj = await self.env.ARTIFACTS.head(GUTENBERG_KEY)
            exists = obj is not None
            return Response.json({
                "key": GUTENBERG_KEY,
                "exists": exists,
                "size": int(getattr(obj, "size", 0) or 0) if exists else 0,
            })
        return Response("Streaming Gutenberg example. Try /demo, /events, or /golden.")
