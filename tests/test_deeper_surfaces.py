from __future__ import annotations

from typing import Any

import pytest

import xampler.r2_data_catalog as catalog_module
from tests.test_r2_pythonic import FakeR2BucketBinding, FakeR2Object
from xampler.browser_rendering import ScreenshotRequest
from xampler.d1 import D1Database
from xampler.kv import KVNamespace
from xampler.queues import QueueJob, QueueSendOptions, QueueService
from xampler.r2 import R2Bucket, R2Range
from xampler.r2_data_catalog import R2DataCatalog
from xampler.r2_sql import R2SqlQuery
from xampler.vectorize import Vector, VectorIndex, VectorQuery


@pytest.mark.asyncio
async def test_r2_ranges() -> None:
    bucket = R2Bucket(FakeR2BucketBinding())
    await bucket.put_bytes("alphabet", b"abcdef")

    assert await bucket.get_bytes("alphabet", byte_range=R2Range(offset=2, length=3)) == b"cde"
    assert await bucket.get_bytes("alphabet", byte_range=R2Range(suffix=2)) == b"ef"


class FakeMultipartUpload:
    key = "large.bin"
    uploadId = "upload-1"

    def __init__(self):
        self.parts: list[tuple[int, Any]] = []
        self.aborted = False

    async def uploadPart(self, part_number: int, body: Any) -> dict[str, Any]:  # noqa: N802
        self.parts.append((part_number, body))
        return {"partNumber": part_number, "etag": f"etag-{part_number}"}

    async def complete(self, parts: list[dict[str, Any]]) -> FakeR2Object:
        del parts
        return FakeR2Object("large.bin", b"complete")

    async def abort(self) -> None:
        self.aborted = True


class FakeMultipartBucket(FakeR2BucketBinding):
    def __init__(self):
        super().__init__()
        self.upload = FakeMultipartUpload()

    async def createMultipartUpload(
        self, key: str, options: dict[str, Any] | None = None
    ) -> FakeMultipartUpload:  # noqa: N802
        del key, options
        return self.upload


@pytest.mark.asyncio
async def test_r2_multipart_complete_and_abort() -> None:
    binding = FakeMultipartBucket()
    upload = await R2Bucket(binding).create_multipart_upload("large.bin")
    part = await upload.upload_part(1, b"chunk")
    info = await upload.complete([part])
    assert info.key == "large.bin"
    assert upload.completed is True

    doomed = await R2Bucket(binding).create_multipart_upload("large.bin")
    await doomed.abort()
    assert doomed.aborted is True


class RecordingD1Statement:
    async def run(self) -> dict[str, Any]:
        return {"success": True}


class RecordingD1Binding:
    def __init__(self):
        self.prepared: list[str] = []
        self.batches: list[list[Any]] = []

    def prepare(self, sql: str) -> RecordingD1Statement:
        self.prepared.append(sql)
        return RecordingD1Statement()

    async def batch(self, statements: list[Any]) -> None:
        self.batches.append(statements)


@pytest.mark.asyncio
async def test_d1_execute_splits_statements_and_batch_skips_empty() -> None:
    binding = RecordingD1Binding()
    db = D1Database(binding)
    await db.execute("CREATE TABLE a(id); CREATE INDEX idx ON a(id);")
    assert binding.prepared == ["CREATE TABLE a(id)", "CREATE INDEX idx ON a(id)"]
    await db.batch_run([])
    assert binding.batches == []


class RecordingKVBinding:
    def __init__(self):
        self.puts: list[tuple[str, str, Any]] = []
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def put(self, key: str, value: str, options: Any | None = None) -> None:
        self.values[key] = value
        self.puts.append((key, value, options))

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def list(self, options: Any | None = None) -> dict[str, Any]:
        return {"keys": [{"name": "a"}], "list_complete": False, "cursor": "next"}


@pytest.mark.asyncio
async def test_kv_ttl_and_list_cursor() -> None:
    binding = RecordingKVBinding()
    kv = KVNamespace(binding)
    await kv.key("session").write_text("value", expiration_ttl=60)
    assert binding.puts[0][2] == {"expirationTtl": 60}
    listed = await kv.list(prefix="a", limit=1)
    assert listed.complete is False
    assert listed.cursor == "next"


class RecordingQueueBinding:
    def __init__(self):
        self.sent: list[tuple[Any, Any | None]] = []
        self.batches: list[Any] = []

    async def send(self, body: Any, options: Any | None = None) -> None:
        self.sent.append((body, options))

    async def sendBatch(self, batch: Any) -> None:  # noqa: N802
        self.batches.append(batch)


@pytest.mark.asyncio
async def test_queue_delay_and_batch_send() -> None:
    binding = RecordingQueueBinding()
    service = QueueService(binding)
    await service.send(QueueJob("kind", {"x": 1}), QueueSendOptions(delay_seconds=5))
    await service.send_many([QueueJob("a", {}), QueueJob("b", {})])
    assert binding.sent[0][1] == {"delaySeconds": 5}
    assert len(binding.batches[0]) == 2


class FakeVectorBinding:
    def __init__(self):
        self.deleted: list[str] = []

    async def query(self, values: Any, options: Any) -> dict[str, Any]:
        del values, options
        return {"matches": [{"id": "doc", "score": 0.9, "metadata": {"title": "Doc"}}]}

    async def queryById(self, vector_id: str, options: Any) -> dict[str, Any]:  # noqa: N802
        del options
        return {"matches": [{"id": vector_id, "score": 1.0}]}

    async def getByIds(self, ids: Any) -> dict[str, Any]:  # noqa: N802
        return {"ids": ids}

    async def deleteByIds(self, ids: Any) -> None:  # noqa: N802
        self.deleted = list(ids)

    async def upsert(self, vectors: Any) -> dict[str, Any]:
        return {"count": len(vectors)}

    async def describe(self) -> dict[str, Any]:
        return {"dimensions": 2}


@pytest.mark.asyncio
async def test_vectorize_query_get_delete() -> None:
    binding = FakeVectorBinding()
    index = VectorIndex(binding, dimensions=2)
    assert (await index.query(VectorQuery(values=[1.0, 0.0]))).matches[0].id == "doc"
    assert (await index.query_by_id("doc-1")).matches[0].score == 1.0
    assert await index.get(["doc-1"]) == {"ids": ["doc-1"]}
    await index.delete(["doc-1"])
    assert binding.deleted == ["doc-1"]
    assert await index.upsert([Vector("doc-2", [0.0, 1.0])]) == {"count": 1}


@pytest.mark.parametrize(
    ("sql", "expected"),
    [
        ("select * from t", "select * from t LIMIT 100"),
        ("select * from t limit 5", "select * from t limit 5"),
        (" explain select * from t; ", "explain select * from t"),
    ],
)
def test_r2_sql_guard_matrix_allowed(sql: str, expected: str) -> None:
    assert R2SqlQuery(sql).safe_sql() == expected


@pytest.mark.parametrize(
    "sql", ["INSERT INTO t VALUES (1)", "SELECT * FROM a JOIN b", "ALTER TABLE t"]
)
def test_r2_sql_guard_matrix_forbidden(sql: str) -> None:
    with pytest.raises(ValueError):
        R2SqlQuery(sql).safe_sql()


def test_browser_rendering_payload() -> None:
    request = ScreenshotRequest(url="https://example.com", full_page=False, image_type="jpeg")
    assert request.payload() == {
        "url": "https://example.com",
        "screenshotOptions": {"fullPage": False, "type": "jpeg"},
    }


class FakeCatalogResponse:
    status = 200

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    async def json(self) -> dict[str, Any]:
        return self.payload


class FakeCatalogJs:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def fetch(self, url: str, init: dict[str, Any]) -> FakeCatalogResponse:
        self.calls.append((url, init))
        return FakeCatalogResponse({"ok": True})


@pytest.mark.asyncio
async def test_r2_data_catalog_paths_and_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCatalogJs()
    monkeypatch.setattr(catalog_module, "js", fake)
    catalog = R2DataCatalog(uri="https://catalog.example", token="secret")
    await catalog.create_table("xampler", "smoke")
    url, init = fake.calls[0]
    assert url == "https://catalog.example/v1/namespaces/xampler/tables"
    assert init["method"] == "POST"
    assert init["headers"]["authorization"] == "Bearer secret"
    assert '"name": "smoke"' in init["body"]
