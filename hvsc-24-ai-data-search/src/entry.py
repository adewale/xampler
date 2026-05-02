from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import d1_null, is_js_missing, to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

HVSC_ARCHIVE_KEY = "hvsc/archives/HVSC_84-all-of-them.7z"
HVSC_ARCHIVE_URL = "https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z"
HVSC_ARCHIVE_SIZE = 83_748_140

HVSC_VERSION_84 = {
    "version": 84,
    "source": "https://www.hvsc.c64.org/api/v1/version/7z",
    "update": {
        "requiredVersion": 83,
        "url": "https://boswme.home.xs4all.nl/HVSC/HVSC_Update_84.7z",
    },
    "complete": {"url": "https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z"},
    "description": "High Voltage SID Collection release metadata for Commodore 64 SID music.",
}


@dataclass(frozen=True)
class HvscRelease:
    version: int
    source: str
    update_url: str
    complete_url: str
    description: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> HvscRelease:
        return cls(
            version=int(data["version"]),
            source=str(data.get("source", "https://www.hvsc.c64.org/api/v1/version/7z")),
            update_url=str(data["update"]["url"]),
            complete_url=str(data["complete"]["url"]),
            description=str(data.get("description", "High Voltage SID Collection release")),
        )


@dataclass(frozen=True)
class IngestJob:
    kind: str
    version: int
    r2_key: str


@dataclass(frozen=True)
class SearchResult:
    version: int
    summary: str
    score: float
    update_url: str
    complete_url: str


@dataclass(frozen=True)
class ArchiveVerification:
    key: str
    source_url: str
    expected_size: int
    stored_size: int
    verified: bool


class R2Artifacts:
    def __init__(self, raw: Any):
        self.raw = raw

    async def write_json(self, key: str, value: Any) -> None:
        await self.raw.put(
            key,
            json.dumps(value),
            to_js({"httpMetadata": {"contentType": "application/json"}}),
        )

    async def read_json(self, key: str) -> Any | None:
        obj = await self.raw.get(key)
        if is_js_missing(obj):
            return None
        return json.loads(str(await obj.text()))

    async def stream_from_url(self, *, url: str, key: str) -> ArchiveVerification:
        response = await js.fetch(url)
        expected_size = int(response.headers.get("content-length") or 0)
        await self.raw.put(
            key,
            response.body,
            to_js({"httpMetadata": {"contentType": "application/x-7z-compressed"}}),
        )
        return await self.verify_archive(key=key, url=url, expected_size=expected_size)

    async def verify_archive(
        self,
        *,
        key: str,
        url: str = HVSC_ARCHIVE_URL,
        expected_size: int = HVSC_ARCHIVE_SIZE,
    ) -> ArchiveVerification:
        obj = await self.raw.head(key)
        stored_size = 0 if is_js_missing(obj) else int(obj.size)
        return ArchiveVerification(
            key=key,
            source_url=url,
            expected_size=expected_size,
            stored_size=stored_size,
            verified=stored_size == expected_size,
        )


class D1Database:
    def __init__(self, raw: Any):
        self.raw = raw

    async def execute(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        stmt = self.raw.prepare(sql)
        if params:
            stmt = stmt.bind(*[d1_null(param) for param in params])
        result = to_py(await stmt.all())
        return list(result.get("results", []))

    async def save_release(self, release: HvscRelease, summary: str) -> None:
        await self.execute(
            "INSERT OR REPLACE INTO releases "
            "(version, source, update_url, complete_url, summary) VALUES (?, ?, ?, ?, ?)",
            release.version,
            release.source,
            release.update_url,
            release.complete_url,
            summary,
        )

    async def search(self, query: str) -> list[SearchResult]:
        rows = await self.execute(
            "SELECT version, summary, update_url, complete_url "
            "FROM releases WHERE summary LIKE ? ORDER BY version DESC LIMIT 10",
            f"%{query}%",
        )
        return [
            SearchResult(
                version=int(row["version"]),
                summary=str(row["summary"]),
                score=1.0,
                update_url=str(row["update_url"]),
                complete_url=str(row["complete_url"]),
            )
            for row in rows
        ]


class QueueService:
    def __init__(self, raw: Any):
        self.raw = raw

    async def send(self, job: IngestJob) -> None:
        await self.raw.send(to_js(asdict(job)))


class ReleaseSummarizer:
    async def summarize(self, release: HvscRelease) -> str:
        return (
            f"HVSC #{release.version} indexes Commodore 64 SID music downloads; "
            f"update archive {PurePosixPath(release.update_url).name}; complete archive "
            f"{PurePosixPath(release.complete_url).name}."
        )


class DemoVectorIndex:
    def embed(self, text: str) -> list[float]:
        text = text.lower()
        return [
            float("hvsc" in text),
            float("sid" in text),
            float("commodore" in text or "c64" in text),
        ]

    def score(self, query: str, document: str) -> float:
        q = self.embed(query)
        d = self.embed(document)
        return sum(a * b for a, b in zip(q, d, strict=True))


class HvscPipeline:
    def __init__(self, env: Any):
        self.r2 = R2Artifacts(env.ARTIFACTS)
        self.db = D1Database(env.DB)
        self.queue = QueueService(env.INGEST_QUEUE)
        self.summarizer = ReleaseSummarizer()
        self.vector = DemoVectorIndex()

    async def ingest(self, release: HvscRelease) -> dict[str, Any]:
        key = f"hvsc/releases/{release.version}.json"
        summary = await self.summarizer.summarize(release)
        await self.r2.write_json(key, asdict(release))
        await self.db.save_release(release, summary)
        await self.queue.send(IngestJob("hvsc-release-index", release.version, key))
        return {"version": release.version, "r2_key": key, "summary": summary}

    async def ingest_archive(self) -> ArchiveVerification:
        return await self.r2.stream_from_url(url=HVSC_ARCHIVE_URL, key=HVSC_ARCHIVE_KEY)

    async def verify_archive(self) -> ArchiveVerification:
        return await self.r2.verify_archive(key=HVSC_ARCHIVE_KEY)

    async def search(self, query: str) -> list[SearchResult]:
        results = await self.db.search(query)
        return [
            SearchResult(
                version=result.version,
                summary=result.summary,
                score=self.vector.score(query, result.summary),
                update_url=result.update_url,
                complete_url=result.complete_url,
            )
            for result in results
        ]


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        query = parse_qs(urlparse(str(request.url)).query)
        pipeline = HvscPipeline(self.env)

        if path == "/":
            return Response(index_html(), headers={"content-type": "text/html; charset=utf-8"})

        if path == "/ingest-fixture":
            return Response.json(await pipeline.ingest(HvscRelease.from_api(HVSC_VERSION_84)))

        if path == "/archive/ingest":
            return Response.json(asdict(await pipeline.ingest_archive()))

        if path == "/archive/verify":
            return Response.json(asdict(await pipeline.verify_archive()))

        if path == "/search":
            term = query.get("q", ["sid"])[0]
            results = [asdict(result) for result in await pipeline.search(term)]
            return Response.json({"query": term, "results": results})

        return Response("Not found", status=404)

    async def queue(self, batch: Any, env: Any, ctx: Any) -> None:
        for message in batch.messages:
            print(f"indexed HVSC job {to_py(message.body)}")
            message.ack()


def index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HVSC AI/Data Pipeline</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px; }
    body { margin: 3rem auto; padding: 0 1rem; }
    button { margin: .25rem; padding: .7rem 1rem; border: 0; }
    button { border-radius: .5rem; background: #2563eb; color: white; cursor: pointer; }
    button.secondary { background: #475569; }
    input { padding: .65rem; min-width: 14rem; }
    pre { background: #0f172a; color: #e2e8f0; padding: 1rem; }
    pre { border-radius: .5rem; overflow: auto; }
  </style>
</head>
<body>
  <h1>HVSC AI/data pipeline</h1>
  <p>Use real HVSC release metadata to exercise R2, D1, Queues, and AI/Vectorize seams.</p>

  <p>
    <button onclick="ingest()">1. Ingest HVSC fixture</button>
    <button class="secondary" onclick="search('sid')">Search SID</button>
    <button class="secondary" onclick="search('commodore')">Search Commodore</button>
    <button class="secondary" onclick="search('hvsc')">Search HVSC</button>
  </p>

  <p>
    <button onclick="archiveIngest()">Optional: stream full 80 MiB archive to R2</button>
    <button class="secondary" onclick="archiveVerify()">Verify archive in R2</button>
  </p>

  <p>
    <input id="q" value="sid" aria-label="search query">
    <button onclick="search(document.getElementById('q').value)">Search custom query</button>
  </p>

  <pre id="output">Click “Ingest HVSC fixture”, then search.</pre>

  <script>
    async function show(response) {
      const text = await response.text();
      try {
        document.getElementById('output').textContent = JSON.stringify(JSON.parse(text), null, 2);
      } catch {
        document.getElementById('output').textContent = text;
      }
    }
    async function ingest() {
      await show(await fetch('/ingest-fixture', { method: 'POST' }));
    }
    async function search(q) {
      await show(await fetch('/search?q=' + encodeURIComponent(q)));
    }
    async function archiveIngest() {
      document.getElementById('output').textContent = 'Streaming ~80 MiB archive to local R2...';
      await show(await fetch('/archive/ingest', { method: 'POST' }));
    }
    async function archiveVerify() {
      await show(await fetch('/archive/verify'));
    }
  </script>
</body>
</html>"""
