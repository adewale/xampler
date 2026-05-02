from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import d1_null, is_js_missing, to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

HVSC_ARCHIVE_KEY = "hvsc/84/raw/HVSC_84-all-of-them.7z"
HVSC_ARCHIVE_URL = "https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z"
HVSC_ARCHIVE_SIZE = 83_748_140
HVSC_CATALOG_KEY = "hvsc/84/catalog/tracks.jsonl"
HVSC_SHARDS_PREFIX = "hvsc/84/catalog/shards/"

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
class Track:
    id: str
    version: int
    path: str
    filename: str
    title: str | None
    composer: str | None
    search_text: str


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


@dataclass(frozen=True)
class CatalogVerification:
    key: str
    size: int
    exists: bool


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
        text = await self.read_text(key)
        return None if text is None else json.loads(text)

    async def read_text(self, key: str) -> str | None:
        obj = await self.raw.get(key)
        if is_js_missing(obj):
            return None
        return str(await obj.text())

    async def verify_catalog(self, key: str = HVSC_CATALOG_KEY) -> CatalogVerification:
        obj = await self.raw.head(key)
        exists = not is_js_missing(obj)
        return CatalogVerification(key=key, size=int(obj.size) if exists else 0, exists=exists)

    async def list_keys(self, prefix: str) -> list[str]:
        data = to_py(await self.raw.list(to_js({"prefix": prefix})))
        return [str(item["key"]) for item in data.get("objects", [])]

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

    async def save_track(self, track: Track) -> None:
        await self.execute(
            "INSERT OR REPLACE INTO tracks "
            "(id, version, path, filename, title, composer, search_text) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            track.id,
            track.version,
            track.path,
            track.filename,
            track.title,
            track.composer,
            track.search_text,
        )

    async def save_ingest_state(
        self,
        *,
        status: str,
        shard_keys: list[str],
        completed_shards: int = 0,
        imported_rows: int = 0,
    ) -> None:
        await self.execute(
            "INSERT OR REPLACE INTO ingest_state "
            "(dataset, status, total_shards, completed_shards, imported_rows, shard_keys) "
            "VALUES ('hvsc-84', ?, ?, ?, ?, ?)",
            status,
            len(shard_keys),
            completed_shards,
            imported_rows,
            json.dumps(shard_keys),
        )

    async def get_ingest_state(self) -> dict[str, Any]:
        rows = await self.execute("SELECT * FROM ingest_state WHERE dataset = 'hvsc-84'")
        if not rows:
            return {
                "status": "not_started",
                "total_shards": 0,
                "completed_shards": 0,
                "imported_rows": 0,
                "shard_keys": [],
            }
        row = rows[0]
        return {
            "status": row["status"],
            "total_shards": int(row["total_shards"]),
            "completed_shards": int(row["completed_shards"]),
            "imported_rows": int(row["imported_rows"]),
            "shard_keys": json.loads(str(row["shard_keys"])),
        }

    async def search_tracks(self, query: str) -> list[Track]:
        rows = await self.execute(
            "SELECT id, version, path, filename, title, composer, search_text "
            "FROM tracks WHERE search_text LIKE ? ORDER BY path LIMIT 20",
            f"%{query}%",
        )
        return [Track(**row) for row in rows]

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

    async def verify_catalog(self, key: str = HVSC_CATALOG_KEY) -> CatalogVerification:
        return await self.r2.verify_catalog(key)

    async def start_ingest(self, prefix: str = HVSC_SHARDS_PREFIX) -> dict[str, Any]:
        shard_keys = await self.r2.list_keys(prefix)
        shard_keys = sorted(key for key in shard_keys if key.endswith(".jsonl"))
        if not shard_keys:
            return {"status": "error", "error": f"no shards found at {prefix}"}
        await self.db.save_ingest_state(status="running", shard_keys=shard_keys)
        return await self.db.get_ingest_state()

    async def ingest_next_shard(self) -> dict[str, Any]:
        state = await self.db.get_ingest_state()
        keys = list(state["shard_keys"])
        completed = int(state["completed_shards"])
        if completed >= len(keys):
            await self.db.save_ingest_state(
                status="complete",
                shard_keys=keys,
                completed_shards=completed,
                imported_rows=int(state["imported_rows"]),
            )
            return await self.db.get_ingest_state()
        result = await self.ingest_catalog_from_r2(key=keys[completed])
        imported_rows = int(state["imported_rows"]) + int(result.get("tracks", 0))
        status = "complete" if completed + 1 >= len(keys) else "running"
        await self.db.save_ingest_state(
            status=status,
            shard_keys=keys,
            completed_shards=completed + 1,
            imported_rows=imported_rows,
        )
        return await self.db.get_ingest_state()

    async def ingest_status(self) -> dict[str, Any]:
        return await self.db.get_ingest_state()

    async def ingest_catalog_from_r2(
        self,
        *,
        key: str = HVSC_CATALOG_KEY,
        limit: int = 0,
    ) -> dict[str, Any]:
        text = await self.r2.read_text(key)
        if text is None:
            return {"key": key, "tracks": 0, "error": "catalog object not found in R2"}

        count = 0
        for line in text.splitlines():
            if not line.strip():
                continue
            await self.db.save_track(Track(**json.loads(line)))
            count += 1
            if limit and count >= limit:
                break
        return {"key": key, "tracks": count, "limited": bool(limit)}

    async def catalog_status(self) -> dict[str, Any]:
        catalog = await self.verify_catalog()
        rows = await self.db.execute("SELECT COUNT(*) AS count FROM tracks")
        return {
            "catalog_key": catalog.key,
            "catalog_exists_in_r2": catalog.exists,
            "catalog_size": catalog.size,
            "d1_tracks": int(rows[0]["count"]) if rows else 0,
        }

    async def search_tracks(self, query: str) -> list[Track]:
        return await self.db.search_tracks(query)

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
            release_result = await pipeline.ingest(HvscRelease.from_api(HVSC_VERSION_84))
            return Response.json({"release": release_result})

        if path == "/ingest/start":
            prefix = query.get("prefix", [HVSC_SHARDS_PREFIX])[0]
            return Response.json(await pipeline.start_ingest(prefix))

        if path == "/ingest/next":
            return Response.json(await pipeline.ingest_next_shard())

        if path == "/ingest/status":
            return Response.json(await pipeline.ingest_status())

        if path == "/catalog/status":
            return Response.json(await pipeline.catalog_status())

        if path == "/catalog/verify-r2":
            key = query.get("key", [HVSC_CATALOG_KEY])[0]
            return Response.json(asdict(await pipeline.verify_catalog(key)))

        if path == "/catalog/ingest-r2":
            key = query.get("key", [HVSC_CATALOG_KEY])[0]
            limit = int(query.get("limit", ["0"])[0] or 0)
            result = await pipeline.ingest_catalog_from_r2(key=key, limit=limit)
            return Response.json(result)

        if path == "/archive/ingest":
            return Response.json(asdict(await pipeline.ingest_archive()))

        if path == "/archive/verify":
            return Response.json(asdict(await pipeline.verify_archive()))

        if path == "/tracks":
            term = query.get("q", ["jeroen"])[0]
            tracks = [asdict(track) for track in await pipeline.search_tracks(term)]
            status = await pipeline.catalog_status()
            response = {"query": term, "tracks": tracks, "status": status}
            if not tracks:
                response["hint"] = (
                    "No D1 track rows matched. Run scripts/hvsc_full_pipeline.py "
                    "to unpack the real archive, build the catalog, and import D1."
                )
            return Response.json(response)

        if path == "/search":
            term = query.get("q", ["sid"])[0]
            release_results = [asdict(result) for result in await pipeline.search(term)]
            track_results = [asdict(track) for track in await pipeline.search_tracks(term)]
            return Response.json(
                {"query": term, "results": release_results, "tracks": track_results}
            )

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
    button.done { background: #16a34a; }
    button.running { background: #ca8a04; }
    button.failed { background: #dc2626; }
    #runAll { display: block; width: 100%; font-size: 1.1rem; margin: 1rem 0; }
    input { padding: .65rem; min-width: 14rem; }
    pre { background: #0f172a; color: #e2e8f0; padding: 1rem; }
    pre { border-radius: .5rem; overflow: auto; }
    .progress { background: #e2e8f0; border-radius: 999px; overflow: hidden; height: 1rem; }
    .bar { background: #16a34a; height: 100%; width: 0%; transition: width .2s; }
    #progressText { margin: .5rem 0 1rem; color: #334155; }
  </style>
</head>
<body>
  <h1>HVSC AI/data pipeline</h1>
  <p>Use real HVSC release metadata to exercise R2, D1, Queues, and AI/Vectorize seams.</p>
  <p>The 80 MiB archive itself is not text-searchable until you unpack it locally,
  build a JSONL catalog, and upload that catalog to R2. These buttons verify each step.</p>

  <button id="runAll" onclick="runAll()">▶ Run all dataset checks and prepare search</button>

  <ol>
    <li>
      <button id="step1" onclick="archiveVerify()">1. Verify full archive object in R2</button>
    </li>
    <li>
      <button id="step2" onclick="ingest()">2. Ingest release metadata + sample</button>
    </li>
    <li>
      <button id="step3" onclick="catalogVerify()">3. Verify catalog JSONL in R2</button>
    </li>
    <li>
      <button id="step4" onclick="shardedIngest()">4. Import all R2 catalog shards into D1</button>
    </li>
    <li>
      <input id="q" value="maniacs" aria-label="search query">
      <button id="step5" onclick="search(document.getElementById('q').value)">
        5. Search D1 catalog
      </button>
    </li>
  </ol>

  <details>
    <summary>Optional setup / stress test buttons</summary>
    <p>
      <button onclick="archiveIngest()">Stream full 80 MiB archive from HVSC to R2</button>
      <button class="secondary" onclick="catalogSample()">Ingest bundled sample only</button>
      <button class="secondary" onclick="search('sid')">Search SID</button>
      <button class="secondary" onclick="search('commodore')">Search Commodore</button>
      <button class="secondary" onclick="search('hvsc')">Search HVSC</button>
      <button class="secondary" onclick="search('maniacs')">Search Maniacs</button>
    </p>
  </details>

  <p>
    <label>Catalog R2 key: <input id="catalogKey" value="hvsc/84/catalog/tracks.jsonl"></label>
    <label>Import limit: <input id="limit" value="0"></label>
  </p>

  <div class="progress"><div id="progressBar" class="bar"></div></div>
  <p id="progressText">0% — not started</p>
  <pre id="output">Start at button 1. Use button 4 after uploading catalog JSONL to R2.</pre>

  <script>
    async function show(response) {
      const text = await response.text();
      try {
        const data = JSON.parse(text);
        document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        return data;
      } catch {
        document.getElementById('output').textContent = text;
        return text;
      }
    }
    function setStep(id, state) {
      const el = document.getElementById(id);
      if (!el) return;
      el.classList.remove('done', 'running', 'failed');
      if (state) el.classList.add(state);
      if (state === 'done') el.textContent = '✓ ' + el.textContent.replace(/^[✓▶✗] /, '');
      if (state === 'running') el.textContent = '▶ ' + el.textContent.replace(/^[✓▶✗] /, '');
      if (state === 'failed') el.textContent = '✗ ' + el.textContent.replace(/^[✓▶✗] /, '');
    }
    function setProgress(done, total, rows) {
      const percent = total ? Math.floor((done / total) * 100) : 0;
      document.getElementById('progressBar').style.width = percent + '%';
      document.getElementById('progressText').textContent =
        percent + '% — ' + done + ' / ' + total + ' shards, ' + rows + ' rows imported';
    }
    async function step(id, fn) {
      setStep(id, 'running');
      try {
        const result = await fn();
        setStep(id, 'done');
        return result;
      } catch (error) {
        setStep(id, 'failed');
        throw error;
      }
    }
    function catalogKey() {
      return encodeURIComponent(document.getElementById('catalogKey').value);
    }
    function limit() {
      return encodeURIComponent(document.getElementById('limit').value || '0');
    }
    async function ingest() {
      return await show(await fetch('/ingest-fixture', { method: 'POST' }));
    }
    async function catalogSample() {
      return await show(await fetch('/catalog/ingest-sample', { method: 'POST' }));
    }
    async function catalogVerify() {
      return await show(await fetch('/catalog/verify-r2?key=' + catalogKey()));
    }
    async function catalogIngest() {
      document.getElementById('output').textContent = 'Pulling catalog JSONL from R2 into D1...';
      const path = '/catalog/ingest-r2?key=' + catalogKey();
      const params = '&limit=' + limit();
      return await show(await fetch(path + params, { method: 'POST' }));
    }
    async function shardedIngest() {
      let state = await show(await fetch('/ingest/start', { method: 'POST' }));
      if (state.error) throw new Error(state.error);
      setProgress(state.completed_shards, state.total_shards, state.imported_rows);
      while (state.status !== 'complete') {
        const msg = 'Importing shard ' + (state.completed_shards + 1) + ' of ';
        document.getElementById('output').textContent = msg + state.total_shards;
        state = await show(await fetch('/ingest/next', { method: 'POST' }));
        setProgress(state.completed_shards, state.total_shards, state.imported_rows);
        await new Promise(resolve => setTimeout(resolve, 25));
      }
      return state;
    }
    async function search(q) {
      return await show(await fetch('/tracks?q=' + encodeURIComponent(q)));
    }
    async function archiveIngest() {
      document.getElementById('output').textContent = 'Streaming ~80 MiB archive to local R2...';
      return await show(await fetch('/archive/ingest', { method: 'POST' }));
    }
    async function archiveVerify() {
      return await show(await fetch('/archive/verify'));
    }
    async function runAll() {
      const runButton = document.getElementById('runAll');
      runButton.disabled = true;
      runButton.className = 'running';
      runButton.textContent = '▶ Running dataset checks...';
      try {
        await step('step1', archiveVerify);
        await step('step2', ingest);
        await step('step3', catalogVerify);
        await step('step4', catalogIngest);
        await step('step5', () => search(document.getElementById('q').value || 'maniacs'));
        runButton.className = 'done';
        runButton.textContent = '✓ Dataset ready — arbitrary D1 catalog search is enabled';
      } catch (error) {
        runButton.className = 'failed';
        runButton.textContent = '✗ Setup failed — see output';
        document.getElementById('output').textContent = String(error);
      } finally {
        runButton.disabled = false;
      }
    }
  </script>
</body>
</html>"""
