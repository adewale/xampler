from __future__ import annotations

from typing import Any

import pytest

from xampler.ai import DemoAIService, TextGenerationRequest, TextGenerationResponse
from xampler.browser_rendering import DemoBrowserRendering, ScreenshotRequest
from xampler.d1 import D1Database
from xampler.kv import KVNamespace
from xampler.queues import QueueConsumer, QueueJob, QueueService
from xampler.r2_data_catalog import DemoR2DataCatalog
from xampler.r2_sql import DemoR2SqlClient, R2SqlQuery
from xampler.vectorize import DemoVectorIndex, VectorIndex, unit_vector


class FakeD1Statement:
    def __init__(self, sql: str, rows: list[dict[str, Any]]):
        self.sql = sql
        self.rows = rows
        self.params: tuple[Any, ...] = ()

    def bind(self, *params: Any) -> FakeD1Statement:
        child = FakeD1Statement(self.sql, self.rows)
        child.params = params
        return child

    async def all(self) -> dict[str, Any]:
        return {"results": self.rows}

    async def run(self) -> dict[str, Any]:
        return {"success": True}


class FakeD1Binding:
    def __init__(self):
        self.rows = [{"quote": "Beautiful is better than ugly", "author": "PEP 20"}]
        self.batches: list[list[Any]] = []

    def prepare(self, sql: str) -> FakeD1Statement:
        return FakeD1Statement(sql, self.rows)

    async def batch(self, statements: list[Any]) -> None:
        self.batches.append(statements)


@pytest.mark.asyncio
async def test_d1_statement_helpers() -> None:
    db = D1Database(FakeD1Binding())
    row = await db.statement("SELECT quote, author FROM quotes").one()
    assert row == {"quote": "Beautiful is better than ugly", "author": "PEP 20"}

    class Quote:
        def __init__(self, quote: str, author: str):
            self.quote = quote
            self.author = author

    quote = await db.statement("SELECT quote, author FROM quotes").one_as(Quote)
    assert quote is not None
    assert quote.author == "PEP 20"


class FakeKVBinding:
    def __init__(self):
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def put(self, key: str, value: str, options: Any | None = None) -> None:
        del options
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def list(self, options: Any | None = None) -> dict[str, Any]:
        del options
        return {"keys": [{"name": key} for key in sorted(self.values)], "list_complete": True}


@pytest.mark.asyncio
async def test_kv_key_helpers() -> None:
    kv = KVNamespace(FakeKVBinding())
    key = kv.key("profile:ada")
    await key.write_json({"name": "Ada"})
    assert await key.read_json() == {"name": "Ada"}
    assert await key.exists() is True
    listed = await kv.list()
    assert listed.keys == ["profile:ada"]
    await key.delete()
    assert await key.exists() is False


class FakeQueueBinding:
    def __init__(self):
        self.sent: list[Any] = []

    async def send(self, body: Any, options: Any | None = None) -> None:
        self.sent.append((body, options))

    async def sendBatch(self, batch: Any) -> None:  # noqa: N802 - Cloudflare API name
        self.sent.append(batch)


class FakeQueueMessage:
    def __init__(self, body: dict[str, Any], attempts: int = 0):
        self.body = body
        self.attempts = attempts
        self.acked = False
        self.retried = False

    def ack(self) -> None:
        self.acked = True

    def retry(self, options: Any) -> None:
        del options
        self.retried = True


class FakeQueueBatch:
    def __init__(self, messages: list[FakeQueueMessage]):
        self.messages = messages


@pytest.mark.asyncio
async def test_queue_service_and_consumer() -> None:
    binding = FakeQueueBinding()
    service = QueueService(binding)
    await service.send(QueueJob("demo", {"source": "test"}))
    assert binding.sent

    message = FakeQueueMessage({"kind": "fail", "payload": {"source": "test"}})
    result = await QueueConsumer().process_batch(FakeQueueBatch([message]))
    assert result.retried == 1
    assert message.retried is True


@pytest.mark.asyncio
async def test_vectorize_demo_and_validation() -> None:
    demo = DemoVectorIndex()
    result = await demo.search(unit_vector(0), top_k=1)
    assert result.matches[0].id == "doc-1"

    index = VectorIndex(raw=object(), dimensions=32)
    index.validate(unit_vector(0))
    with pytest.raises(ValueError):
        index.validate([1.0, 2.0])


@pytest.mark.asyncio
async def test_ai_demo_and_response_parsing() -> None:
    request = TextGenerationRequest("hello")
    result = await DemoAIService().generate_text(request)
    assert "hello" in result.text
    parsed = TextGenerationResponse.from_workers_ai({"result": {"response": "nested"}})
    assert parsed.text == "nested"


@pytest.mark.asyncio
async def test_r2_sql_guard_and_demo() -> None:
    assert R2SqlQuery("select * from table").safe_sql().endswith("LIMIT 100")
    assert R2SqlQuery("SHOW TABLES IN xampler").safe_sql() == "SHOW TABLES IN xampler"
    with pytest.raises(ValueError):
        R2SqlQuery("DROP TABLE x").safe_sql()
    result = await DemoR2SqlClient().query(R2SqlQuery("SHOW DATABASES"))
    assert result.data["rows"][0]["bucket"] == "demo"


@pytest.mark.asyncio
async def test_r2_data_catalog_demo_and_paths() -> None:
    demo = DemoR2DataCatalog()
    namespaces = await demo.list_namespaces()
    assert {item["name"] for item in namespaces["namespaces"]} == {"hvsc", "examples"}
    lifecycle = await demo.lifecycle("xampler_verify", "temp_table")
    assert lifecycle["lifecycle_complete"] is True


@pytest.mark.asyncio
async def test_browser_rendering_demo() -> None:
    result = await DemoBrowserRendering().screenshot(ScreenshotRequest(url="https://example.com"))
    assert result.source == "demo-browser-rendering"
    assert result.image_type == "png"
