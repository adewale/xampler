from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

from cfboundary.ffi import d1_null, to_js, to_py
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

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
        if obj is None:
            return None
        return json.loads(str(await obj.text()))


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
            return Response("HVSC AI/data pipeline: POST /ingest-fixture then GET /search?q=sid\n")

        if path == "/ingest-fixture":
            return Response.json(await pipeline.ingest(HvscRelease.from_api(HVSC_VERSION_84)))

        if path == "/search":
            term = query.get("q", ["sid"])[0]
            results = [asdict(result) for result in await pipeline.search(term)]
            return Response.json({"query": term, "results": results})

        return Response("Not found", status=404)

    async def queue(self, batch: Any, env: Any, ctx: Any) -> None:
        for message in batch.messages:
            print(f"indexed HVSC job {to_py(message.body)}")
            message.ack()
