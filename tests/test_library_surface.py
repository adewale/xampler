from __future__ import annotations

from typing import Any

import pytest

from xampler.ai import DemoAIService, TextGenerationRequest, TextGenerationResponse
from xampler.browser_rendering import DemoBrowserRendering, ScreenshotRequest
from xampler.errors import XamplerError
from xampler.queues import QueueConsumer, QueueJob, QueueService
from xampler.r2_data_catalog import DemoR2DataCatalog
from xampler.r2_sql import DemoR2SqlClient, R2SqlQuery
from xampler.vectorize import DemoVectorIndex, VectorIndex, unit_vector


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
        self.retried: Any = None

    def ack(self) -> None:
        self.acked = True

    def retry(self, options: Any) -> None:
        self.retried = options


class FakeQueueBatch:
    def __init__(self, messages: list[FakeQueueMessage]):
        self.messages = messages


@pytest.mark.asyncio
async def test_queue_service_and_consumer() -> None:
    binding = FakeQueueBinding()
    service = QueueService(binding)
    await service.send(QueueJob("demo", {"source": "test"}))
    assert binding.sent == [({"kind": "demo", "payload": {"source": "test"}}, None)]

    ok = FakeQueueMessage({"kind": "ok", "payload": {}})
    failing = FakeQueueMessage({"kind": "fail", "payload": {"source": "test"}}, attempts=2)
    result = await QueueConsumer().process_batch(FakeQueueBatch([ok, failing]))
    assert (result.processed, result.retried) == (1, 1)
    assert (ok.acked, ok.retried) == (True, None)
    # Exponential backoff: 30s * 2**attempts.
    assert (failing.acked, failing.retried) == (False, {"delaySeconds": 120})


@pytest.mark.asyncio
async def test_vectorize_demo_and_validation() -> None:
    demo = DemoVectorIndex()
    result = await demo.search(unit_vector(0), top_k=1)
    assert result.matches[0].id == "doc-1"

    index = VectorIndex(raw=object(), dimensions=32)
    index.validate(unit_vector(0))
    with pytest.raises(XamplerError) as exc_info:
        index.validate([1.0, 2.0])
    assert exc_info.value.code == "bad_request"


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
    with pytest.raises(XamplerError) as exc_info:
        R2SqlQuery("DROP TABLE x").safe_sql()
    assert exc_info.value.code == "bad_request"
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
