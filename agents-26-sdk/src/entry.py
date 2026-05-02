from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import asdict, dataclass
from typing import Any, Protocol
from urllib.parse import parse_qs, urlparse

from workers import DurableObject, Response, WorkerEntrypoint  # type: ignore[import-not-found]


@dataclass(frozen=True)
class AgentMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AgentToolCall:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass(frozen=True)
class AgentRunResult:
    agent: str
    messages: list[AgentMessage]
    tool_calls: list[AgentToolCall]
    final: str
    status: str = "complete"


class AgentTool(Protocol):
    name: str

    async def run(self, **kwargs: Any) -> dict[str, Any]: ...


class WeatherTool:
    name = "weather.lookup"

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        city = str(kwargs.get("city", "Lagos"))
        return {"city": city, "forecast": "sunny", "temperature_c": 29}


class DemoAgent:
    def __init__(self, *, name: str, tools: list[AgentTool]):
        self.name = name
        self.tools = {tool.name: tool for tool in tools}
        self.raw = None

    async def run(self, message: str) -> AgentRunResult:
        messages = [AgentMessage("user", message)]
        city = "Lagos"
        if "london" in message.lower():
            city = "London"
        tool = self.tools["weather.lookup"]
        weather = await tool.run(city=city)
        call = AgentToolCall(tool.name, {"city": city}, weather)
        final = f"{city} is {weather['forecast']} at {weather['temperature_c']}°C."
        messages.append(AgentMessage("assistant", final))
        return AgentRunResult(self.name, messages, [call], final)


class AgentSession:
    def __init__(self, raw: Any):
        self.raw = raw

    async def run(self, message: str) -> dict[str, Any]:
        response = await self.raw.fetch(
            "https://agent.local/run",
            {"method": "POST", "body": json.dumps({"message": message})},
        )
        return await response.json()


class AgentDurableObject(DurableObject):
    def __init__(self, state: Any, env: Any):
        super().__init__(state, env)
        self.agent = DemoAgent(name="durable-demo-agent", tools=[WeatherTool()])

    async def fetch(self, request: Any) -> Response:
        body = "{}"
        with suppress(Exception):
            body = await request.text()
        payload = json.loads(body or "{}")
        message = str(payload.get("message", "weather in Lagos"))
        result = await self.agent.run(message)
        return Response.json(asdict(result))


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        parsed = urlparse(str(request.url))
        query = parse_qs(parsed.query)
        message = query.get("message", ["weather in Lagos"])[0]

        if parsed.path == "/demo":
            result = await DemoAgent(name="demo-agent", tools=[WeatherTool()]).run(message)
            return Response.json(asdict(result))

        if parsed.path.startswith("/agents/") and parsed.path.endswith("/run"):
            name = parsed.path.split("/")[2]
            stub = self.env.AGENT.get(self.env.AGENT.idFromName(name))
            return await stub.fetch(request)

        return Response("Agents SDK example. Try /demo?message=weather%20in%20Lagos.")
