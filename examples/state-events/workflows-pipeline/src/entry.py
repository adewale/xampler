# ruff: noqa: E501
from __future__ import annotations

import asyncio
import html
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint, WorkflowEntrypoint  # type: ignore[import-not-found]

from xampler.d1 import D1Database
from xampler.response import jsonable
from xampler.workflows import DemoWorkflowService, WorkflowService


class Pipeline(WorkflowEntrypoint):
    """A small DAG workflow with named durable steps."""

    async def run(self, event: Any, step: Any) -> None:
        @step.do("fetch input")
        async def fetch_input() -> str:
            await asyncio.sleep(0)
            return "input"

        @step.do("transform", depends=[fetch_input])
        async def transform(value: str = "input") -> str:
            return value.upper()

        @step.do("summarize", depends=[transform])
        async def summarize(value: str = "INPUT") -> None:
            print(f"Workflow complete: {value}")

        await summarize()


async def record_timeline(db: D1Database, instance_id: str) -> None:
    now = datetime.now(UTC).isoformat()
    steps = [
        ("fetch input", "complete", "r2://input", {"records": 3}),
        ("transform", "complete", "batch:1", {"records": 3}),
        ("summarize", "complete", "final", {"summary": "INPUT"}),
    ]
    await db.statement("DELETE FROM workflow_timeline WHERE instance_id = ?").run(instance_id)
    for step, state, checkpoint, details in steps:
        await db.statement(
            """
            INSERT INTO workflow_timeline (
              instance_id, step, state, checkpoint, details, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
        ).run(instance_id, step, state, checkpoint, json.dumps(details), now)


async def timeline(db: D1Database, instance_id: str) -> dict[str, Any]:
    rows = await db.query(
        """
        SELECT step, state, checkpoint, details, created_at
        FROM workflow_timeline
        WHERE instance_id = ?
        ORDER BY id
        """,
        instance_id,
    )
    events = [
        {
            **row,
            "details": json.loads(str(row.get("details") or "{}")),
        }
        for row in rows
    ]
    return {"instance_id": instance_id, "events": events, "count": len(events)}


def html_page(body: str) -> Response:
    page = """<!doctype html>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Workflow Timeline · Xampler</title>
<style>
*{box-sizing:border-box}body{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1120px;margin:0 auto;padding:2rem 1rem;color:#17202a;background:linear-gradient(180deg,#f8fafc,#fff 20rem)}a{color:#2563eb}h1{font-size:clamp(2.1rem,5vw,3.2rem);line-height:1.04;margin:.1rem 0 .75rem;letter-spacing:-.04em}h2{font-size:1.05rem;margin:0 0 .45rem}.eyebrow{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:800}.hero{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:1.5rem;align-items:end;border-bottom:1px solid #d0d7de;padding-bottom:1.3rem;margin-bottom:1.4rem}.lede{font-size:1.1rem;color:#334155;max-width:72ch}.card,.step,.panel{border:1px solid #d0d7de;border-radius:16px;background:rgba(255,255,255,.9);box-shadow:0 8px 24px rgba(15,23,42,.05)}.card{padding:1rem}.layout{display:grid;grid-template-columns:340px minmax(0,1fr);gap:1.4rem;align-items:start}.workflow{position:sticky;top:1rem;display:grid;gap:1rem}.step{padding:1rem}.num{display:inline-grid;place-items:center;width:1.65rem;height:1.65rem;border-radius:999px;background:#2563eb;color:white;font-weight:800;font-size:.85rem;margin-right:.45rem}.muted{color:#64748b}.button-row{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:.8rem}button{font:inherit;padding:.55rem .8rem;border:1px solid #2563eb;border-radius:10px;background:#2563eb;color:white;cursor:pointer;font-weight:650}button.secondary{background:white;color:#2563eb}button:disabled{opacity:.65;cursor:wait}.panel{overflow:hidden}.panel-head{display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:1rem;border-bottom:1px solid #e2e8f0;background:#f8fafc}.status{display:inline-flex;gap:.45rem;align-items:center;border:1px solid #cbd5e1;border-radius:999px;padding:.3rem .55rem;background:white;color:#475569;font-size:.86rem}.dot{width:.55rem;height:.55rem;border-radius:999px;background:#94a3b8}.status.running .dot{background:#2563eb}.status.ok .dot{background:#16a34a}.status.error .dot{background:#dc2626}.timeline{padding:1rem;display:grid;gap:.75rem}.event{display:grid;grid-template-columns:1.2rem minmax(0,1fr);gap:.75rem;align-items:start}.event-dot{width:.9rem;height:.9rem;border-radius:999px;background:#16a34a;margin-top:.35rem}.event-card{border:1px solid #e2e8f0;border-radius:12px;padding:.85rem;background:white}.event-card strong{display:block}.chips{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.45rem}.chip{border-radius:999px;background:#dcfce7;color:#14532d;padding:.14rem .5rem;font-size:.84rem}.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;padding:1rem;border-bottom:1px solid #e2e8f0}.metric{border:1px solid #e2e8f0;border-radius:12px;padding:.8rem;background:white}.metric strong{display:block;font-size:1.35rem}pre{margin:0;padding:1rem;background:#0d1117;color:#e6edf3;overflow:auto;white-space:pre-wrap;max-height:24rem}.raw{border-top:1px solid #e2e8f0}.raw summary{cursor:pointer;padding:.75rem 1rem;background:#f8fafc}@media(max-width:860px){body{padding:1rem}.hero,.layout{display:block}.workflow{position:static;margin-bottom:1rem}.metrics{grid-template-columns:1fr}}
</style>
__BODY__"""
    return Response(page.replace("__BODY__", body), headers={"content-type": "text/html; charset=utf-8"})


def index_html() -> Response:
    return html_page(
        """
<header class=hero><div><p class=eyebrow>State and events example</p><h1>Workflow Timeline</h1><p class=lede>Start a deterministic local workflow, record each durable step into D1, and inspect the timeline as a product-style status page instead of raw endpoint JSON.</p></div><aside class=card><strong>What this proves</strong><p class=muted>Workers Workflows orchestration plus a D1 sidecar for searchable, auditable progress events.</p></aside></header>
<main class=layout><aside class=workflow><section class=step><h2><span class=num>1</span>Start local demo</h2><p class=muted>Creates a stable demo instance and writes three timeline events.</p><div class=button-row><button id=start>Start demo workflow</button></div></section><section class=step><h2><span class=num>2</span>Inspect status</h2><p class=muted>Fetches workflow status and the D1 timeline for the current instance.</p><div class=button-row><button id=refresh class=secondary>Refresh timeline</button><a href=/demo/start>JSON endpoint</a></div></section></aside><section class=panel><div class=panel-head><div><h2>Timeline dashboard</h2><p class=muted id=instance>Instance: none yet</p></div><span id=status class=status><span class=dot></span><span>Ready</span></span></div><div class=metrics><div class=metric><span class=muted>Steps</span><strong id=steps>—</strong></div><div class=metric><span class=muted>State</span><strong id=state>—</strong></div><div class=metric><span class=muted>Checkpoint</span><strong id=checkpoint>—</strong></div></div><div id=timeline class=timeline><div class=event-card><strong>Start with “Start demo workflow”.</strong><p class=muted>The page uses AJAX to run the same verified routes without losing context.</p></div></div><details class=raw><summary>Raw JSON</summary><pre id=out>{"hint":"Click Start demo workflow."}</pre></details></section></main>
<script>
let currentInstance = 'demo-instance';
const statusEl = document.querySelector('#status');
function setStatus(kind, text){ statusEl.className = 'status ' + kind; statusEl.querySelector('span:last-child').textContent = text; }
function esc(value){ return String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function render(timeline, started){
  document.querySelector('#instance').textContent = 'Instance: ' + timeline.instance_id;
  document.querySelector('#steps').textContent = timeline.count;
  const last = timeline.events[timeline.events.length - 1] || {};
  document.querySelector('#state').textContent = last.state || started?.status || 'complete';
  document.querySelector('#checkpoint').textContent = last.checkpoint || '—';
  document.querySelector('#timeline').innerHTML = timeline.events.map(e => '<div class=event><span class=event-dot></span><div class=event-card><strong>' + esc(e.step) + '</strong><p class=muted>' + esc(e.created_at) + '</p><div class=chips><span class=chip>' + esc(e.state) + '</span><span class=chip>' + esc(e.checkpoint) + '</span></div></div></div>').join('');
  document.querySelector('#out').textContent = JSON.stringify({started, timeline}, null, 2);
}
async function loadTimeline(startFirst){
  setStatus('running', 'Running…');
  try {
    const started = startFirst ? await (await fetch('/demo/start')).json() : null;
    if (started) currentInstance = started.instance_id;
    const timeline = await (await fetch('/timeline/' + currentInstance)).json();
    render(timeline, started);
    setStatus('ok', 'Complete');
  } catch (err) {
    document.querySelector('#out').textContent = JSON.stringify({error:String(err)}, null, 2);
    setStatus('error', 'Error');
  }
}
document.querySelector('#start').onclick = () => loadTimeline(true);
document.querySelector('#refresh').onclick = () => loadTimeline(false);
</script>
"""
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = urlparse(str(request.url))
        db = D1Database(self.env.DB)

        if url.path == "/":
            return index_html()

        if url.path == "/demo/start":
            started = await DemoWorkflowService().start()
            await record_timeline(db, started.instance_id)
            return Response.json(jsonable(started))

        if url.path.startswith("/timeline/"):
            instance_id = url.path.removeprefix("/timeline/")
            return Response.json(await timeline(db, instance_id))

        if url.path.startswith("/demo/status/"):
            instance_id = url.path.removeprefix("/demo/status/")
            return Response.json(jsonable(await DemoWorkflowService().status(instance_id)))

        service = WorkflowService(self.env.PIPELINE)
        if url.path == "/start":
            return Response.json(jsonable(await service.start()))

        if url.path.startswith("/status/"):
            instance_id = url.path.removeprefix("/status/")
            return Response.json(jsonable(await service.status(instance_id)))

        return html_page(f"<h2>Not found</h2><p>{html.escape(url.path)}</p>")
