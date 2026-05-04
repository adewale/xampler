from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.d1 import D1Database as XamplerD1Database
from xampler.queues import QueueJob, QueueService
from xampler.r2 import R2Bucket
from xampler.streaming import JsonlReader
from xampler.vectorize import DemoVectorIndex

HVSC_ARCHIVE_KEY = "hvsc/84/raw/HVSC_84-all-of-them.7z"
HVSC_ARCHIVE_URL = "https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z"
HVSC_ARCHIVE_SIZE = 83_748_140
HVSC_CATALOG_KEY = "hvsc/84/catalog/tracks.jsonl"
HVSC_SHARDS_PREFIX = "hvsc/84/catalog/shards/"
HVSC_SAMPLE_CATALOG_KEY = "hvsc/84/catalog/sample.jsonl"
HVSC_SAMPLE_CATALOG = [
    {
        "id": "hvsc:84:jeroen_tel:cybernoid_ii",
        "version": 84,
        "path": "MUSICIANS/J/Jeroen_Tel/Cybernoid_II.sid",
        "filename": "Cybernoid_II.sid",
        "title": "Cybernoid II",
        "composer": "Jeroen Tel",
        "search_text": "Jeroen Tel Cybernoid II Commodore 64 C64 SID",
    },
    {
        "id": "hvsc:84:maniacs_of_noise:last_ninja_3",
        "version": 84,
        "path": "MUSICIANS/M/Maniacs_of_Noise/Last_Ninja_3.sid",
        "filename": "Last_Ninja_3.sid",
        "title": "Last Ninja 3",
        "composer": "Maniacs of Noise",
        "search_text": "Maniacs of Noise Last Ninja 3 Commodore 64 C64 SID",
    },
]
HVSC_SAMPLE_CATALOG_JSONL = "\n".join(json.dumps(record) for record in HVSC_SAMPLE_CATALOG)

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


class R2Artifacts(R2Bucket):
    async def write_json(self, key: str, value: Any) -> None:
        await self.put_text(key, json.dumps(value), content_type="application/json")

    async def verify_catalog(self, key: str = HVSC_CATALOG_KEY) -> CatalogVerification:
        info = await self.head(key)
        return CatalogVerification(
            key=key,
            size=0 if info is None or info.size is None else info.size,
            exists=info is not None,
        )

    async def list_keys(self, prefix: str) -> list[str]:
        return [item.key async for item in self.iter_objects(prefix=prefix)]

    async def stream_from_url(self, *, url: str, key: str) -> ArchiveVerification:
        response = await js.fetch(url)
        expected_size = int(response.headers.get("content-length") or 0)
        await self.put_stream(key, response.body, content_type="application/x-7z-compressed")
        return await self.verify_archive(key=key, url=url, expected_size=expected_size)

    async def verify_archive(
        self,
        *,
        key: str,
        url: str = HVSC_ARCHIVE_URL,
        expected_size: int = HVSC_ARCHIVE_SIZE,
    ) -> ArchiveVerification:
        info = await self.head(key)
        stored_size = 0 if info is None or info.size is None else info.size
        return ArchiveVerification(
            key=key,
            source_url=url,
            expected_size=expected_size,
            stored_size=stored_size,
            verified=stored_size == expected_size,
        )


class HvscDatabase(XamplerD1Database):
    async def execute_rows(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        return await self.query(sql, *params)

    async def save_release(self, release: HvscRelease, summary: str) -> None:
        await self.execute_rows(
            "INSERT OR REPLACE INTO releases "
            "(version, source, update_url, complete_url, summary) VALUES (?, ?, ?, ?, ?)",
            release.version,
            release.source,
            release.update_url,
            release.complete_url,
            summary,
        )

    async def save_track(self, track: Track) -> None:
        await self.execute_rows(
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
        await self.execute_rows(
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
        rows = await self.execute_rows("SELECT * FROM ingest_state WHERE dataset = 'hvsc-84'")
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
        rows = await self.execute_rows(
            "SELECT id, version, path, filename, title, composer, search_text "
            "FROM tracks WHERE search_text LIKE ? ORDER BY path LIMIT 20",
            f"%{query}%",
        )
        return [Track(**row) for row in rows]

    async def search(self, query: str) -> list[SearchResult]:
        rows = await self.execute_rows(
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


class ReleaseSummarizer:
    async def summarize(self, release: HvscRelease) -> str:
        return (
            f"HVSC #{release.version} indexes Commodore 64 SID music downloads; "
            f"update archive {PurePosixPath(release.update_url).name}; complete archive "
            f"{PurePosixPath(release.complete_url).name}."
        )


class HvscPipeline:
    def __init__(self, env: Any):
        self.r2 = R2Artifacts(env.ARTIFACTS)
        self.db = HvscDatabase(env.DB)
        self.queue = QueueService(env.INGEST_QUEUE)
        self.summarizer = ReleaseSummarizer()
        self.vector = DemoVectorIndex()

    async def ingest(self, release: HvscRelease) -> dict[str, Any]:
        key = f"hvsc/releases/{release.version}.json"
        summary = await self.summarizer.summarize(release)
        await self.r2.write_json(key, asdict(release))
        await self.db.save_release(release, summary)
        job = IngestJob("hvsc-release-index", release.version, key)
        await self.queue.send(QueueJob(job.kind, asdict(job)))
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

    async def ingest_sample_catalog(self) -> dict[str, Any]:
        await self.r2.put_text(
            HVSC_SAMPLE_CATALOG_KEY,
            HVSC_SAMPLE_CATALOG_JSONL,
            content_type="application/x-ndjson",
        )
        return await self.ingest_catalog_from_r2(key=HVSC_SAMPLE_CATALOG_KEY)

    async def ingest_catalog_from_r2(
        self,
        *,
        key: str = HVSC_CATALOG_KEY,
        limit: int = 0,
    ) -> dict[str, Any]:
        catalog = await self.r2.verify_catalog(key)
        if not catalog.exists:
            return {"key": key, "tracks": 0, "error": "catalog object not found in R2"}

        count = 0
        stream = await self.r2.byte_stream(key)
        records = JsonlReader(stream.iter_lines()).records()
        async for record in records:
            await self.db.save_track(Track(**record))
            count += 1
            if limit and count >= limit:
                break
        return {"key": key, "tracks": count, "limited": bool(limit), "streamed": True}

    async def catalog_status(self) -> dict[str, Any]:
        catalog = await self.verify_catalog()
        rows = await self.db.query("SELECT COUNT(*) AS count FROM tracks")
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

        if path == "/catalog/ingest-sample":
            return Response.json(await pipeline.ingest_sample_catalog())

        if path == "/archive/ingest":
            return Response.json(asdict(await pipeline.ingest_archive()))

        if path == "/archive/verify":
            return Response.json(asdict(await pipeline.verify_archive()))

        if path == "/tracks":
            term = query.get("q", ["jeroen"])[0]
            tracks = [asdict(track) for track in await pipeline.search_tracks(term)]
            status = await pipeline.catalog_status()
            response = {
                "query": term,
                "count": len(tracks),
                "tracks": tracks,
                "status": status,
                "ready": int(status["d1_tracks"]) > 0,
            }
            if not tracks:
                response["hint"] = (
                    "No D1 track rows matched. Click the browser run-all button or call "
                    "POST /ingest/start then POST /ingest/next until complete to import "
                    "the published R2 shard catalog into local D1."
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
    #results { margin: 1rem 0; }
    .result { border: 1px solid #cbd5e1; border-radius: .6rem; padding: .8rem; }
    .result + .result { margin-top: .6rem; }
    .result h3 { margin: 0 0 .25rem; font-size: 1rem; }
    .result p { margin: .2rem 0; color: #334155; }
    .muted { color: #64748b; }
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
      <form id="searchForm">
        <input id="q" value="maniacs" aria-label="search query" autocomplete="off">
        <button id="step5" type="submit">5. Search D1 catalog</button>
      </form>
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
  <div id="results" aria-live="polite">
    <p class="muted">Search results will appear here after the catalog is imported.</p>
  </div>
  <pre id="output">Start at button 1. Use button 4 after uploading catalog JSONL to R2.</pre>

  <script>
    function output(text) {
      const el = document.getElementById('output');
      if (el.textContent !== text) el.textContent = text;
    }
    function compactIngestState(data) {
      if (!data || !Array.isArray(data.shard_keys)) return data;
      const copy = { ...data };
      copy.shard_count = data.shard_keys.length;
      copy.first_shard = data.shard_keys[0] || null;
      copy.last_shard = data.shard_keys[data.shard_keys.length - 1] || null;
      delete copy.shard_keys;
      return copy;
    }
    async function readResponse(response) {
      const text = await response.text();
      let data = text;
      try { data = JSON.parse(text); } catch {}
      if (!response.ok) {
        const message = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
        const error = new Error(message);
        error.status = response.status;
        throw error;
      }
      return data;
    }
    async function show(response, options = {}) {
      const data = await readResponse(response);
      const rendered = options.compactIngest ? compactIngestState(data) : data;
      output(typeof rendered === 'string' ? rendered : JSON.stringify(rendered, null, 2));
      return data;
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
    async function ingestNextWithRetry() {
      for (let attempt = 0; attempt < 5; attempt++) {
        try {
          return await readResponse(await fetch('/ingest/next', { method: 'POST' }));
        } catch (error) {
          if (error.status === 503 || String(error).toLowerCase().includes('restart')) {
            output('Worker restarted mid-import; retrying shard...');
            await new Promise(resolve => setTimeout(resolve, 1000));
            continue;
          }
          throw error;
        }
      }
      throw new Error('Worker kept restarting during shard import. Try again.');
    }
    async function shardedIngest() {
      let state = await show(await fetch('/ingest/start', { method: 'POST' }), {
        compactIngest: true,
      });
      if (state.error) {
        if (String(state.error).includes('no shards found')) {
          output(
            state.error + '\\n\\n' +
            'No prebuilt full-catalog shards are present in local R2, so the ' +
            'playground is importing the bundled sample catalog instead. Run ' +
            '`uv run python scripts/hvsc_full_pipeline.py --bucket xampler-datasets` ' +
            'from the repo root to prepare the full shard set.'
          );
          const sample = await catalogSample();
          const rows = Number(sample.tracks || 0);
          setProgress(1, 1, rows);
          return {
            status: 'complete',
            fallback: 'sample-catalog',
            total_shards: 1,
            completed_shards: 1,
            imported_rows: rows,
            sample,
          };
        }
        throw new Error(state.error);
      }
      setProgress(state.completed_shards, state.total_shards, state.imported_rows);
      let lastRenderedShard = state.completed_shards;
      while (state.status !== 'complete') {
        if (state.completed_shards !== lastRenderedShard) {
          const next = Math.min(state.completed_shards + 1, state.total_shards);
          output('Importing shard ' + next + ' of ' + state.total_shards + '...');
          lastRenderedShard = state.completed_shards;
        }
        state = await ingestNextWithRetry();
        setProgress(state.completed_shards, state.total_shards, state.imported_rows);
        await new Promise(resolve => setTimeout(resolve, 25));
      }
      output(JSON.stringify(compactIngestState(state), null, 2));
      return state;
    }
    function setResults(html) {
      document.getElementById('results').innerHTML = html;
    }
    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[char]));
    }
    function renderSearch(data) {
      const query = escapeHtml(data.query || '');
      const status = data.status || {};
      if (!data.ready) {
        setResults('<p class="muted">Preparing the catalog before searching…</p>');
        return;
      }
      if (!data.tracks || data.tracks.length === 0) {
        setResults('<p>No HVSC tracks matched <strong>' + query + '</strong>.</p>');
        return;
      }
      const rows = data.tracks.map(track => (
        '<article class="result">' +
          '<h3>' + escapeHtml(track.title || track.filename) + '</h3>' +
          '<p><strong>File:</strong> ' + escapeHtml(track.path) + '</p>' +
          (track.composer ? '<p><strong>Composer:</strong> ' +
            escapeHtml(track.composer) + '</p>' : '') +
        '</article>'
      )).join('');
      setResults(
        '<p>Showing ' + data.tracks.length + ' of ' + status.d1_tracks +
        ' imported tracks matching <strong>' + query + '</strong>.</p>' + rows
      );
    }
    async function search(q) {
      const term = (q || '').trim();
      if (!term) {
        setResults('<p class="muted">Enter a search term.</p>');
        return null;
      }
      let data = await show(await fetch('/tracks?q=' + encodeURIComponent(term)));
      if (!data.ready) {
        setResults(
          '<p class="muted">Preparing the full HVSC catalog in local D1. ' +
          'Search will run automatically when import finishes.</p>'
        );
        await step('step4', shardedIngest);
        data = await show(await fetch('/tracks?q=' + encodeURIComponent(term)));
      }
      renderSearch(data);
      return data;
    }
    async function archiveIngest() {
      document.getElementById('output').textContent = 'Streaming ~80 MiB archive to local R2...';
      return await show(await fetch('/archive/ingest', { method: 'POST' }));
    }
    async function archiveVerify() {
      return await show(await fetch('/archive/verify'));
    }
    document.getElementById('searchForm').addEventListener('submit', event => {
      event.preventDefault();
      step('step5', () => search(document.getElementById('q').value));
    });
    async function refreshStatus() {
      try {
        const state = await readResponse(await fetch('/ingest/status'));
        setProgress(state.completed_shards, state.total_shards, state.imported_rows);
        if (state.status === 'complete') {
          setResults(
            '<p class="muted">Catalog ready. Try searches like jeroen, maniacs, ' +
            'hubbard, or galway.</p>'
          );
        }
      } catch {}
    }
    refreshStatus();
    async function runAll() {
      const runButton = document.getElementById('runAll');
      runButton.disabled = true;
      runButton.className = 'running';
      runButton.textContent = '▶ Running dataset checks...';
      try {
        await step('step1', archiveVerify);
        await step('step2', ingest);
        await step('step3', catalogVerify);
        await step('step4', shardedIngest);
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
