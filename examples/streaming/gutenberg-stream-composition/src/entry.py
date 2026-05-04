# ruff: noqa: E501
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
from cfboundary.ffi import is_js_missing, to_js_bytes, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.ai import DemoAIService
from xampler.d1 import D1Database, D1Statement
from xampler.response import jsonable
from xampler.status import BatchResult, Checkpoint, Progress
from xampler.streaming import (
    AgentEvent,
    ByteStream,
    JsonlReader,
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


async def bytes_from_text(text: str, chunk_size: int = 48) -> AsyncIterator[bytes]:
    data = text.encode()
    for offset in range(0, len(data), chunk_size):
        yield data[offset : offset + chunk_size]


class DemoD1Sink:
    def __init__(self) -> None:
        self.rows: list[TextRecord] = []
        self.checkpoint = Checkpoint("gutenberg-demo", 0, 0)

    async def insert_batch(self, rows: list[TextRecord]) -> None:
        self.rows.extend(rows)
        self.checkpoint = Checkpoint(
            "gutenberg-demo",
            offset=self.checkpoint.offset + len(rows),
            records=len(self.rows),
        )

    async def complete(self) -> Checkpoint:
        self.checkpoint = Checkpoint(
            self.checkpoint.name,
            self.checkpoint.offset,
            self.checkpoint.records,
            "complete",
        )
        return self.checkpoint


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


def index_html() -> Response:
    return Response(
        """<!doctype html>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Gutenberg Streaming · Xampler</title>
<style>
*{box-sizing:border-box}body{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1180px;margin:0 auto;padding:2rem 1rem;color:#17202a;background:linear-gradient(180deg,#f8fafc,#fff 22rem)}
a{color:#2563eb}.hero{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:1.5rem;align-items:end;border-bottom:1px solid #d0d7de;padding-bottom:1.4rem;margin-bottom:1.5rem}.eyebrow{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:800;margin:0 0 .35rem}h1{font-size:clamp(2.1rem,5vw,3.5rem);line-height:1.03;margin:.1rem 0 .8rem;letter-spacing:-.04em}h2{font-size:1.05rem;margin:0 0 .55rem}.lede{font-size:1.1rem;color:#334155;max-width:72ch}.route-card,.panel,.step{border:1px solid #d0d7de;border-radius:16px;background:rgba(255,255,255,.88);box-shadow:0 8px 24px rgba(15,23,42,.05)}.route-card{padding:1rem}.route-card code{display:block;margin-top:.45rem;overflow-wrap:anywhere}.layout{display:grid;grid-template-columns:360px minmax(0,1fr);gap:1.5rem;align-items:start}.workflow{position:sticky;top:1rem;display:grid;gap:1rem}.step{padding:1rem}.step-num{display:inline-grid;place-items:center;width:1.65rem;height:1.65rem;border-radius:999px;background:#2563eb;color:white;font-weight:800;font-size:.85rem;margin-right:.45rem}.muted{color:#64748b}.button-row{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:.8rem}button{font:inherit;padding:.55rem .8rem;border:1px solid #2563eb;border-radius:10px;background:#2563eb;color:white;cursor:pointer;font-weight:650}button.secondary{background:white;color:#2563eb}button:disabled{opacity:.6;cursor:wait}input{font:inherit;border:1px solid #cbd5e1;border-radius:10px;padding:.55rem .7rem;width:100%;min-width:0}.main{display:grid;gap:1rem}.panel{overflow:hidden}.panel-head{display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:1rem;border-bottom:1px solid #e2e8f0;background:#f8fafc}.status{display:inline-flex;gap:.45rem;align-items:center;border:1px solid #cbd5e1;border-radius:999px;padding:.3rem .55rem;background:white;color:#475569;font-size:.86rem}.dot{width:.55rem;height:.55rem;border-radius:999px;background:#94a3b8}.status.running .dot{background:#2563eb}.status.ok .dot{background:#16a34a}.status.error .dot{background:#dc2626}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.75rem;padding:1rem}.metric{border:1px solid #e2e8f0;border-radius:12px;padding:.8rem;background:white}.metric strong{display:block;font-size:1.35rem}.results{padding:1rem;display:grid;gap:.75rem}.result{border:1px solid #e2e8f0;border-radius:12px;padding:.85rem;background:white}.result mark{background:#fde68a;color:#111827;border-radius:4px;padding:0 .1rem}.output-wrap{border-top:1px solid #e2e8f0}.output-head{display:flex;justify-content:space-between;align-items:center;padding:.75rem 1rem;background:#f8fafc}pre{margin:0;padding:1rem;background:#0d1117;color:#e6edf3;overflow:auto;white-space:pre-wrap;max-height:34rem;min-height:12rem}.diagram{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.45rem;margin-top:1rem}.node{border:1px solid #bfdbfe;background:#eff6ff;color:#1e3a8a;border-radius:12px;padding:.65rem;text-align:center;font-size:.9rem;font-weight:700}.arrow{align-self:center;text-align:center;color:#64748b}.tabs{display:flex;gap:.5rem;flex-wrap:wrap;padding:1rem;border-bottom:1px solid #e2e8f0}.tabs button{background:white;color:#2563eb}.tabs button.active{background:#2563eb;color:white}.hidden{display:none!important}@media(max-width:900px){body{padding:1rem}.hero,.layout{display:block}.workflow{position:static;margin-bottom:1rem}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.diagram{grid-template-columns:1fr}.arrow{display:none}}
</style>
<header class=hero>
  <div>
    <p class=eyebrow>Streaming composition example</p>
    <h1>Gutenberg Streaming Composition</h1>
    <p class=lede>This app turns a Project Gutenberg ZIP in R2 into streamable text, indexes it in D1 FTS, and records checkpointed ingestion progress. Use it left-to-right: inspect the object, build the index, search, then run the checkpointed line pipeline.</p>
    <div class=diagram aria-label="pipeline diagram"><div class=node>R2 ZIP</div><div class=arrow>→</div><div class=node>byte stream</div><div class=arrow>→</div><div class=node>D1 FTS + checkpoints</div></div>
  </div>
  <aside class=route-card><strong>What this proves</strong><code>ByteStream.iter_lines()</code><code>aiter_batches()</code><code>R2 object bodies</code><code>D1 batch writes + FTS5</code></aside>
</header>
<main class=layout>
  <aside class=workflow>
    <section class=step><h2><span class=step-num>1</span>Inspect the archive</h2><p class=muted>Downloads the Shakespeare ZIP into local R2 if missing, then reports stream and archive metadata.</p><div class=button-row><button data-action=/zip-demo>Inspect R2 ZIP</button><button class=secondary data-action=/golden>R2 status</button></div></section>
    <section class=step><h2><span class=step-num>2</span>Build searchable text</h2><p class=muted>Extracts HTML, converts it to text chunks, writes chunks and FTS rows to D1 in batches.</p><div class=button-row><button data-action=/fts/ingest>Build FTS</button><button class=secondary data-action=/fts/status>FTS status</button></div></section>
    <section class=step><h2><span class=step-num>3</span>Search the index</h2><p class=muted>Try Shakespeare terms after building FTS.</p><input id=q value="romeo juliet" aria-label="Search query"><div class=button-row><button id=search>Search</button><button class=secondary data-action=/fts/verify>Verify queries</button></div></section>
    <section class=step><h2><span class=step-num>4</span>Run checkpointed ingest</h2><p class=muted>Persists line-level progress into D1 so a streaming pipeline can expose resumable status.</p><div class=button-row><button data-action=/pipeline/ingest-r2-lines>Ingest lines</button><button class=secondary data-action=/pipeline/status>Status</button></div></section>
  </aside>
  <section class=main>
    <section class=panel>
      <div class=panel-head><div><h2>Dashboard</h2><p class=muted>Run actions with AJAX; the page stays in place while results update.</p></div><span id=status class=status><span class=dot></span><span>Ready</span></span></div>
      <div id=metrics class=metrics>
        <div class=metric><span class=muted>R2 bytes</span><strong>—</strong></div><div class=metric><span class=muted>Chunks</span><strong>—</strong></div><div class=metric><span class=muted>FTS rows</span><strong>—</strong></div><div class=metric><span class=muted>Lines</span><strong>—</strong></div>
      </div>
      <div class=tabs><button class=active data-view=summary>Summary</button><button data-view=search>Search results</button><button data-view=raw>Raw JSON</button></div>
      <div id=summary class=results><div class=result><strong>Start with “Inspect R2 ZIP”.</strong><p class=muted>The verifier also exercises these same routes, including the browser JavaScript on this page.</p></div></div>
      <div id=searchResults class="results hidden"></div>
      <div id=rawWrap class="output-wrap hidden"><div class=output-head><strong>Raw response</strong><button id=copy class=secondary>Copy JSON</button></div><pre id=out>{"hint":"Choose an action from the workflow."}</pre></div>
    </section>
  </section>
</main>
<script>
const statusEl = document.querySelector('#status');
const metricsEl = document.querySelector('#metrics');
const summaryEl = document.querySelector('#summary');
const searchEl = document.querySelector('#searchResults');
const rawWrap = document.querySelector('#rawWrap');
const out = document.querySelector('#out');
let lastJson = {hint: 'Choose an action from the workflow.'};
function setStatus(kind, text) {
  statusEl.className = 'status ' + kind;
  statusEl.querySelector('span:last-child').textContent = text;
}
function esc(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function metric(label, value) {
  return '<div class=metric><span class=muted>' + esc(label) + '</span><strong>' + esc(value ?? '—') + '</strong></div>';
}
function updateMetrics(data) {
  const status = data.status || {};
  const checkpoint = status.checkpoint || {};
  metricsEl.innerHTML = metric('R2 bytes', data.zip_bytes || data.r2_streamed_bytes) + metric('Chunks', data.chunks || status.chunks) + metric('FTS rows', status.fts_rows) + metric('Lines', data.lines || status.lines || checkpoint.records);
}
function renderSummary(path, data) {
  const rows = [];
  if (path.includes('zip-demo') || path.includes('golden')) rows.push(['Archive', data.exists === false ? 'Missing from R2' : 'Available in R2'], ['Key', data.golden_key || data.key], ['ZIP bytes', data.zip_bytes || data.size], ['Stream chunks', data.r2_stream_chunks]);
  else if (path.includes('fts/ingest')) rows.push(['FTS ingest', data.all_chunks_indexed ? 'All chunks indexed' : 'Completed'], ['Chunks', data.chunks], ['Batches', data.batches], ['Text chars', data.source_text_chars]);
  else if (path.includes('pipeline')) rows.push(['Pipeline', data.all_lines_checkpointed ? 'All lines checkpointed' : 'Status loaded'], ['Lines', data.lines || data.status?.lines], ['Batches', data.batches], ['Checkpoint', data.status?.checkpoint?.state || data.checkpoint?.state]);
  else if (path.includes('verify')) rows.push(['Verification', data.all_queries_return_results ? 'All sample searches returned results' : 'Some searches need an index'], ['Chunks indexed', data.all_chunks_indexed], ['Queries', data.queries?.length]);
  else rows.push(['Result', 'Action completed']);
  summaryEl.innerHTML = rows.map(([k,v]) => '<div class=result><strong>' + esc(k) + '</strong><p class=muted>' + esc(v ?? '—') + '</p></div>').join('');
}
function renderSearch(data) {
  const results = data.results || [];
  if (!results.length) { searchEl.innerHTML = '<div class=result><strong>No matches yet.</strong><p class=muted>Build FTS, then search for terms like hamlet, tempest, or romeo juliet.</p></div>'; return; }
  searchEl.innerHTML = results.map(r => '<div class=result><strong>Chunk ' + esc(r.chunk_no) + '</strong><p>' + esc(r.snippet || '').replaceAll('&lt;mark&gt;','<mark>').replaceAll('&lt;/mark&gt;','</mark>') + '</p></div>').join('');
}
function activate(view) {
  document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  summaryEl.classList.toggle('hidden', view !== 'summary');
  searchEl.classList.toggle('hidden', view !== 'search');
  rawWrap.classList.toggle('hidden', view !== 'raw');
}
async function run(path) {
  setStatus('running', 'Running…');
  document.querySelectorAll('button').forEach(b => b.disabled = true);
  try {
    const res = await fetch(path);
    const data = await res.json();
    lastJson = data;
    out.textContent = JSON.stringify(data, null, 2);
    updateMetrics(data);
    renderSummary(path, data);
    if (path.includes('/fts/search')) { renderSearch(data); activate('search'); } else { activate('summary'); }
    setStatus('ok', 'Done');
  } catch (err) {
    lastJson = {error: String(err)};
    out.textContent = JSON.stringify(lastJson, null, 2);
    summaryEl.innerHTML = '<div class=result><strong>Request failed</strong><p class=muted>' + esc(err) + '</p></div>';
    setStatus('error', 'Error');
  } finally {
    document.querySelectorAll('button').forEach(b => b.disabled = false);
  }
}
document.querySelectorAll('[data-action]').forEach(b => b.onclick = () => run(b.dataset.action));
document.querySelector('#search').onclick = () => run('/fts/search?q=' + encodeURIComponent(document.querySelector('#q').value));
document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => activate(b.dataset.view));
document.querySelector('#copy').onclick = async () => navigator.clipboard?.writeText(JSON.stringify(lastJson, null, 2));
</script>""",
        headers={"content-type": "text/html; charset=utf-8"},
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/":
            return index_html()
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
        return index_html()
