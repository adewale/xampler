# ruff: noqa: E501
from __future__ import annotations

import json
import re
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


class CalculatorTool:
    name = "calculator.eval"

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        expression = str(kwargs.get("expression", "2+3"))
        match = re.fullmatch(r"\s*(\d+)\s*([+\-*/])\s*(\d+)\s*", expression)
        if match is None:
            raise ValueError("calculator only accepts simple binary arithmetic")
        left, op, right = match.groups()
        a = int(left)
        b = int(right)
        value = {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[op]
        return {"expression": expression, "value": value}


class SearchTool:
    name = "docs.search"

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        query = str(kwargs.get("query", "workers"))
        corpus = {
            "workers": "Workers run application code at Cloudflare's edge.",
            "d1": "D1 is a serverless SQL database with SQLite semantics.",
        }
        key = "d1" if "d1" in query.lower() else "workers"
        return {"query": query, "hit": key, "snippet": corpus[key]}


class DemoAgent:
    def __init__(self, *, name: str, tools: list[AgentTool]):
        self.name = name
        self.tools = {tool.name: tool for tool in tools}
        self.raw = None

    async def run(self, message: str) -> AgentRunResult:
        messages = [AgentMessage("user", message)]
        calls: list[AgentToolCall] = []
        lower = message.lower()
        if "calculate" in lower or "2+3" in lower:
            expression = "2+3" if "2+3" in message else "40+2"
            result = await self.tools["calculator.eval"].run(expression=expression)
            calls.append(AgentToolCall("calculator.eval", {"expression": expression}, result))
        if "search" in lower or "d1" in lower:
            query = "d1" if "d1" in lower else "workers"
            result = await self.tools["docs.search"].run(query=query)
            calls.append(AgentToolCall("docs.search", {"query": query}, result))
        if not calls:
            city = "London" if "london" in lower else "Lagos"
            weather = await self.tools["weather.lookup"].run(city=city)
            calls.append(AgentToolCall("weather.lookup", {"city": city}, weather))
        final = "; ".join(f"{call.name} -> {call.result}" for call in calls)
        messages.append(AgentMessage("assistant", final))
        return AgentRunResult(self.name, messages, calls, final)


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
        self.agent = DemoAgent(
            name="durable-demo-agent", tools=[WeatherTool(), CalculatorTool(), SearchTool()]
        )

    async def fetch(self, request: Any) -> Response:
        body = "{}"
        with suppress(Exception):
            body = await request.text()
        payload = json.loads(body or "{}")
        message = str(payload.get("message", "weather in Lagos"))
        result = await self.agent.run(message)
        return Response.json(asdict(result))


def index_html() -> Response:
    return Response(
        """<!doctype html>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Agent Tools · Xampler</title>
<style>
body{font:16px/1.55 system-ui;max-width:980px;margin:2rem auto;padding:0 1rem;color:#17202a}header{border-bottom:1px solid #d0d7de;margin-bottom:1rem}textarea{width:100%;min-height:7rem;font:inherit}button{font:inherit;padding:.5rem .8rem;border:1px solid #2563eb;border-radius:.5rem;background:#2563eb;color:white;cursor:pointer}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.card{border:1px solid #d0d7de;border-radius:.75rem;padding:1rem;background:#f8fafc}pre{background:#0d1117;color:#e6edf3;padding:1rem;border-radius:.75rem;overflow:auto}.tool{display:inline-block;background:#dbeafe;color:#1e3a8a;border-radius:999px;padding:.1rem .5rem;margin:.1rem}@media(max-width:760px){.grid{display:block}.card{margin-bottom:1rem}}
</style>
<header><h1>Deterministic Agent Tools</h1><p>Try calculator, search, and weather tools without an LLM dependency.</p></header>
<section class=grid><article class=card><h2>Prompt</h2><textarea id=message>calculate 2+3 and search D1</textarea><p><button id=run>Run agent</button></p><p><span class=tool>calculator.eval</span><span class=tool>docs.search</span><span class=tool>weather.lookup</span></p></article><article class=card><h2>Transcript</h2><pre id=out>Ready.</pre></article></section>
<script>
document.querySelector('#run').onclick = async () => {
 const message = encodeURIComponent(document.querySelector('#message').value);
 const data = await (await fetch('/demo?message=' + message)).json();
 document.querySelector('#out').textContent = JSON.stringify(data, null, 2);
};
</script>""",
        headers={"content-type": "text/html; charset=utf-8"},
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        parsed = urlparse(str(request.url))
        query = parse_qs(parsed.query)
        message = query.get("message", ["weather in Lagos"])[0]

        if parsed.path == "/":
            return index_html()

        if parsed.path == "/demo":
            result = await DemoAgent(
                name="demo-agent", tools=[WeatherTool(), CalculatorTool(), SearchTool()]
            ).run(message)
            return Response.json(asdict(result))

        if parsed.path == "/demo/transcript":
            result = await DemoAgent(
                name="demo-agent", tools=[WeatherTool(), CalculatorTool(), SearchTool()]
            ).run("calculate 2+3 and search D1")
            payload = asdict(result)
            calculator_called = any(call.name == "calculator.eval" for call in result.tool_calls)
            search_called = any(call.name == "docs.search" for call in result.tool_calls)
            payload["assertions"] = {
                "calculator_called": calculator_called,
                "search_called": search_called,
                "transcript_complete": result.status == "complete" and len(result.messages) == 2,
            }
            return Response.json(payload)

        if parsed.path.startswith("/agents/") and parsed.path.endswith("/run"):
            name = parsed.path.split("/")[2]
            stub = self.env.AGENT.get(self.env.AGENT.idFromName(name))
            return await stub.fetch(request)

        return index_html()
