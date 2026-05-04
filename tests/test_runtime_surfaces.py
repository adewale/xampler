from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from xampler.agents import AgentMessage, AgentSession, DemoAgent
from xampler.ai_gateway import ChatMessage, ChatRequest, DemoAIGateway
from xampler.durable_objects import DurableObjectNamespace, DurableObjectRef
from xampler.experimental.cron import DemoScheduledJob, ScheduledEventInfo
from xampler.experimental.service_bindings import DemoServiceBinding
from xampler.experimental.websockets import DemoWebSocketSession
from xampler.response import error_payload, jsonable
from xampler.workflows import DemoWorkflowService, parse_workflow_state


class FakeResponse:
    def __init__(self, body: str):
        self.body = body

    async def text(self) -> str:
        return self.body


class FakeStub:
    def __init__(self):
        self.requests: list[Any] = []

    async def fetch(self, request: Any) -> FakeResponse:
        self.requests.append(request)
        return FakeResponse("7")


class FakeNamespace:
    def __init__(self):
        self.stub = FakeStub()

    def idFromName(self, name: str) -> str:  # noqa: N802 - Cloudflare API name
        return f"id:{name}"

    def get(self, object_id: str) -> FakeStub:
        assert object_id == "id:counter"
        return self.stub


@pytest.mark.asyncio
async def test_durable_object_namespace_and_ref() -> None:
    ref = DurableObjectNamespace(FakeNamespace()).named("counter")
    assert isinstance(ref, DurableObjectRef)
    assert await ref.text("/value") == "7"


@pytest.mark.asyncio
async def test_workflows_demo_and_state_parser() -> None:
    service = DemoWorkflowService()
    started = await service.start()
    assert started.instance_id == "demo-instance"
    assert (await service.status(started.instance_id)).status == "complete"
    assert parse_workflow_state("nonsense") == "running"


@pytest.mark.asyncio
async def test_cron_demo_job() -> None:
    event = SimpleNamespace(cron="*/5 * * * *", scheduledTime=0)
    info = ScheduledEventInfo.from_event(event)
    result = await DemoScheduledJob().run(info)
    assert result.ok is True
    assert result.cron == "*/5 * * * *"


@pytest.mark.asyncio
async def test_service_bindings_and_websockets_demos() -> None:
    rpc = await DemoServiceBinding().call("highlight_code", "print('x')")
    assert rpc.method == "highlight_code"
    status = await DemoWebSocketSession().status()
    assert status.status == "connected"


@pytest.mark.asyncio
async def test_agents_and_ai_gateway_demos() -> None:
    agent = await DemoAgent().run("hello")
    assert agent.messages[-1].role == "assistant"

    class RawAgent:
        async def run(self, message: str) -> AgentMessage:
            return AgentMessage("assistant", message.upper())

    session = await AgentSession(RawAgent()).run("hello")
    assert "HELLO" in session.messages[-1].content

    gateway = await DemoAIGateway().chat(ChatRequest(messages=[ChatMessage("user", "hello")]))
    assert "hello" in gateway.text


def test_response_jsonable_and_error_payload() -> None:
    assert jsonable(AgentMessage("user", "hello")) == {"role": "user", "content": "hello"}
    assert error_payload("nope", status=422)["error"]["status"] == 422
