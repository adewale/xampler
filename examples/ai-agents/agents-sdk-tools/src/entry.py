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
        weather = {
            "Lagos": {"forecast": "sunny", "temperature_c": 29, "humidity": "78%"},
            "London": {"forecast": "light rain", "temperature_c": 14, "humidity": "84%"},
            "Tokyo": {"forecast": "clear", "temperature_c": 23, "humidity": "62%"},
        }
        return {"city": city, **weather.get(city, weather["Lagos"])}


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
            "durable objects": "Durable Objects coordinate stateful rooms, sessions, and actors.",
        }
        lowered = query.lower()
        key = "durable objects" if "durable" in lowered else "d1" if "d1" in lowered else "workers"
        return {"query": query, "hit": key, "snippet": corpus[key], "rank": 1}


class DemoAgent:
    def __init__(self, *, name: str, tools: list[AgentTool]):
        self.name = name
        self.tools = {tool.name: tool for tool in tools}
        self.raw = None

    async def run(self, message: str) -> AgentRunResult:
        messages = [AgentMessage("user", message)]
        calls: list[AgentToolCall] = []
        lower = message.lower()
        expression_match = re.search(r"\b\d+\s*[+\-*/]\s*\d+\b", message)
        if "calculate" in lower or expression_match is not None:
            expression = expression_match.group(0) if expression_match else "40+2"
            result = await self.tools["calculator.eval"].run(expression=expression)
            calls.append(AgentToolCall("calculator.eval", {"expression": expression}, result))
        if "search" in lower or "d1" in lower or "workers" in lower or "durable" in lower:
            query = "durable objects" if "durable" in lower else "d1" if "d1" in lower else "workers"
            result = await self.tools["docs.search"].run(query=query)
            calls.append(AgentToolCall("docs.search", {"query": query}, result))
        if "weather" in lower or "lagos" in lower or "london" in lower or "tokyo" in lower:
            city = "London" if "london" in lower else "Tokyo" if "tokyo" in lower else "Lagos"
            weather = await self.tools["weather.lookup"].run(city=city)
            calls.append(AgentToolCall("weather.lookup", {"city": city}, weather))
        if not calls:
            weather = await self.tools["weather.lookup"].run(city="Lagos")
            calls.append(AgentToolCall("weather.lookup", {"city": "Lagos"}, weather))
        plan = ", ".join(call.name for call in calls)
        messages.append(AgentMessage("assistant", f"Plan: call {plan}."))
        for call in calls:
            messages.append(AgentMessage("tool", f"{call.name}: {call.result}"))
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
*{box-sizing:border-box}body{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1120px;margin:0 auto;padding:2rem 1rem;color:#17202a;background:linear-gradient(180deg,#f8fafc,#fff 20rem)}h1{font-size:clamp(2.1rem,5vw,3.2rem);line-height:1.04;margin:.1rem 0 .75rem;letter-spacing:-.04em}h2{font-size:1.05rem;margin:0 0 .45rem}.eyebrow{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:800}.hero{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:1.5rem;align-items:end;border-bottom:1px solid #d0d7de;padding-bottom:1.3rem;margin-bottom:1.4rem}.lede{font-size:1.1rem;color:#334155;max-width:72ch}.card,.panel,.tool-card{border:1px solid #d0d7de;border-radius:16px;background:rgba(255,255,255,.9);box-shadow:0 8px 24px rgba(15,23,42,.05)}.card{padding:1rem}.layout{display:grid;grid-template-columns:380px minmax(0,1fr);gap:1.4rem;align-items:start}.prompt{position:sticky;top:1rem}.panel{overflow:hidden}.panel-head{display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:1rem;border-bottom:1px solid #e2e8f0;background:#f8fafc}.muted{color:#64748b}textarea{width:100%;min-height:8rem;font:inherit;border:1px solid #cbd5e1;border-radius:12px;padding:.75rem;resize:vertical}button{font:inherit;padding:.55rem .8rem;border:1px solid #2563eb;border-radius:10px;background:#2563eb;color:white;cursor:pointer;font-weight:650}button.secondary{background:white;color:#2563eb}button:disabled{opacity:.65;cursor:wait}.button-row{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:.8rem}.tools{display:grid;gap:.7rem;margin-top:1rem}.tool-card{padding:.85rem}.tool{display:inline-flex;background:#dbeafe;color:#1e3a8a;border-radius:999px;padding:.14rem .55rem;font-size:.86rem;font-weight:700}.status{display:inline-flex;gap:.45rem;align-items:center;border:1px solid #cbd5e1;border-radius:999px;padding:.3rem .55rem;background:white;color:#475569;font-size:.86rem}.dot{width:.55rem;height:.55rem;border-radius:999px;background:#94a3b8}.status.running .dot{background:#2563eb}.status.ok .dot{background:#16a34a}.status.error .dot{background:#dc2626}.transcript{padding:1rem;display:grid;gap:.75rem}.message,.call{border:1px solid #e2e8f0;border-radius:12px;padding:.85rem;background:white}.message strong,.call strong{display:block}.calls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.75rem}.final{border-left:4px solid #16a34a}.quick{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.75rem}pre{margin:0;padding:1rem;background:#0d1117;color:#e6edf3;overflow:auto;white-space:pre-wrap;max-height:22rem}.raw{border-top:1px solid #e2e8f0}.raw summary{cursor:pointer;padding:.75rem 1rem;background:#f8fafc}@media(max-width:860px){body{padding:1rem}.hero,.layout{display:block}.prompt{position:static;margin-bottom:1rem}}
</style>
<header class=hero><div><p class=eyebrow>AI agents example</p><h1>Deterministic Agent Tools</h1><p class=lede>Explore the shape of an agent loop without needing an LLM locally: a prompt selects calculator, docs search, or weather tools, then records a transcript and final answer.</p></div><aside class=card><strong>What this proves</strong><p class=muted>Tool interfaces, Durable Object agent sessions, and browser-friendly transcript rendering.</p></aside></header>
<main class=layout><aside class="card prompt"><h2>Prompt playground</h2><textarea id=message>weather in Lagos, calculate 12*7, and search Durable Objects</textarea><div class=button-row><button id=run>Run local agent</button><button id=durable class=secondary>Run Durable Object session</button></div><div class=quick><button class=secondary data-prompt="weather in Lagos">Weather</button><button class=secondary data-prompt="calculate 12*7">Calculator</button><button class=secondary data-prompt="search Durable Objects and D1">Docs search</button><button class=secondary data-prompt="weather in London, calculate 8*9, and search Workers">Multi-tool</button></div><div class=tools><div class=tool-card><span class=tool>calculator.eval</span><p class=muted>Accepts simple arithmetic such as 12*7 and returns a typed result.</p></div><div class=tool-card><span class=tool>docs.search</span><p class=muted>Returns deterministic Workers, D1, or Durable Objects documentation snippets.</p></div><div class=tool-card><span class=tool>weather.lookup</span><p class=muted>Provides city-specific weather data for Lagos, London, and Tokyo.</p></div></div></aside><section class=panel><div class=panel-head><div><h2>Transcript</h2><p class=muted>Structured output stays readable; raw JSON is still available for debugging.</p></div><span id=status class=status><span class=dot></span><span>Ready</span></span></div><div id=transcript class=transcript><div class=message><strong>Ready.</strong><p class=muted>Run the default prompt to see three tool calls, tool-role messages, and a final answer.</p></div></div><details class=raw><summary>Raw JSON</summary><pre id=out>{"hint":"Run the agent."}</pre></details></section></main>
<script>
const statusEl = document.querySelector('#status');
function setStatus(kind, text){ statusEl.className = 'status ' + kind; statusEl.querySelector('span:last-child').textContent = text; }
function esc(value){ return String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function render(data){
  const messages = (data.messages || []).map(m => '<div class=message><strong>' + esc(m.role) + '</strong><p>' + esc(m.content) + '</p></div>').join('');
  const calls = (data.tool_calls || []).map(c => '<div class=call><strong>' + esc(c.name) + '</strong><p class=muted>args ' + esc(JSON.stringify(c.arguments)) + '</p><p>result ' + esc(JSON.stringify(c.result)) + '</p></div>').join('');
  document.querySelector('#transcript').innerHTML = messages + '<div class=calls>' + calls + '</div><div class="message final"><strong>Final</strong><p>' + esc(data.final) + '</p></div>';
  document.querySelector('#out').textContent = JSON.stringify(data, null, 2);
}
async function run(path){
  setStatus('running', 'Running…');
  try { const data = await (await fetch(path, path.startsWith('/agents/') ? {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({message:document.querySelector('#message').value})} : undefined)).json(); render(data); setStatus('ok', 'Complete'); }
  catch (err) { document.querySelector('#out').textContent = JSON.stringify({error:String(err)}, null, 2); setStatus('error', 'Error'); }
}
document.querySelector('#run').onclick = () => run('/demo?message=' + encodeURIComponent(document.querySelector('#message').value));
document.querySelector('#durable').onclick = () => run('/agents/demo/run');
document.querySelectorAll('[data-prompt]').forEach(b => b.onclick = () => { document.querySelector('#message').value = b.dataset.prompt; });
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
            ).run("weather in Lagos, calculate 12*7, and search Durable Objects")
            payload = asdict(result)
            calculator_called = any(call.name == "calculator.eval" for call in result.tool_calls)
            search_called = any(call.name == "docs.search" for call in result.tool_calls)
            payload["assertions"] = {
                "calculator_called": calculator_called,
                "search_called": search_called,
                "weather_called": any(call.name == "weather.lookup" for call in result.tool_calls),
                "transcript_complete": result.status == "complete" and len(result.messages) >= 5,
            }
            return Response.json(payload)

        if parsed.path.startswith("/agents/") and parsed.path.endswith("/run"):
            name = parsed.path.split("/")[2]
            stub = self.env.AGENT.get(self.env.AGENT.idFromName(name))
            return await stub.fetch(request)

        return index_html()
