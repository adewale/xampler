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
    return Response(
        f"""<!doctype html>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Workflow Timeline · Xampler</title>
<style>
body{{font:16px/1.55 system-ui;max-width:980px;margin:2rem auto;padding:0 1rem;color:#17202a}}
header{{display:flex;justify-content:space-between;gap:1rem;align-items:baseline;border-bottom:1px solid #d0d7de;margin-bottom:1rem}}
a{{color:#2563eb}}button{{font:inherit;padding:.5rem .8rem;border:1px solid #2563eb;border-radius:.5rem;background:#2563eb;color:white;cursor:pointer}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}}.card{{border:1px solid #d0d7de;border-radius:.75rem;padding:1rem;background:#f8fafc}}
pre{{background:#0d1117;color:#e6edf3;padding:1rem;border-radius:.75rem;overflow:auto}}.pill{{display:inline-block;background:#dcfce7;color:#14532d;border-radius:999px;padding:.1rem .5rem}}
</style>
<header><h1>Workflow Timeline</h1><nav><a href=/demo/start>JSON demo</a></nav></header>
{body}""",
        headers={"content-type": "text/html; charset=utf-8"},
    )


def index_html() -> Response:
    return html_page(
        """
<section class=grid>
  <article class=card><h2>Start demo workflow</h2><p>Runs a deterministic local workflow and records ordered D1 timeline events.</p><button id=start>Start demo</button></article>
  <article class=card><h2>Timeline</h2><p>Each step stores state, checkpoint, details, and timestamp.</p><p><span class=pill>D1 sidecar</span></p></article>
</section>
<pre id=out>Click Start demo.</pre>
<script>
document.querySelector('#start').onclick = async () => {
  const started = await (await fetch('/demo/start')).json();
  const timeline = await (await fetch('/timeline/' + started.instance_id)).json();
  document.querySelector('#out').textContent = JSON.stringify({started, timeline}, null, 2);
};
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
