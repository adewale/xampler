# ruff: noqa: E501
from __future__ import annotations

import json
from typing import Any, cast
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.experimental.dynamic_workers import python_fetch_worker, stable_worker_id

COMPATIBILITY_DATE = "2026-05-01"
_CALLBACKS: list[Any] = []

CHILD_SOURCE = """export default {
  fetch(request, env) {
    return new Response(env.MESSAGE || "hello from a Dynamic Worker", {
      headers: { "x-dynamic-worker": "javascript" }
    });
  }
}
"""

NETWORK_TEST_SOURCE = """export default {
  async fetch() {
    try {
      await fetch("https://example.com");
    } catch (err) {
      return new Response("blocked: " + err.constructor.name);
    }
    return new Response("unexpected network access", { status: 500 });
  }
}
"""

PYTHON_CHILD_SOURCE = '''from __future__ import annotations

from typing import Any
import js  # type: ignore[import-not-found]


async def fetch(request: Any, env: Any, ctx: Any) -> Any:
    return js.Response.new("hello from a dynamic Python Worker")
'''


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/":
            return html_response(index_html())
        if path == "/run":
            return await run_dynamic_child(self.env.LOADER, request)
        if path == "/blocked-network":
            return await run_network_check(self.env.LOADER, request)
        if path == "/worker-code":
            code = python_fetch_worker(PYTHON_CHILD_SOURCE, compatibility_date=COMPATIBILITY_DATE)
            return json_response(code.to_raw())
        return Response("not found", status=404)


async def run_dynamic_child(loader: Any, request: Any) -> Response:
    _ = request
    raw = {
        "compatibilityDate": COMPATIBILITY_DATE,
        "mainModule": "worker.js",
        "modules": {"worker.js": CHILD_SOURCE},
        "globalOutbound": None,
        "env": {"MESSAGE": "hello from a Dynamic Worker loaded by Python"},
    }
    worker_id = stable_worker_id("xampler-python-child", json.dumps(raw, sort_keys=True))

    def load_code() -> Any:
        return js_object(raw)

    worker = loader.get(worker_id, keep_callback(load_code))
    return await worker.getEntrypoint().fetch("http://xampler.local/run")


async def run_network_check(loader: Any, request: Any) -> Response:
    _ = request
    raw = {
        "compatibilityDate": COMPATIBILITY_DATE,
        "mainModule": "network.js",
        "modules": {"network.js": NETWORK_TEST_SOURCE},
        "globalOutbound": None,
    }

    def load_code() -> Any:
        return js_object(raw)

    worker = loader.get(
        stable_worker_id("xampler-network-check", json.dumps(raw, sort_keys=True)),
        keep_callback(load_code),
    )
    return await worker.getEntrypoint().fetch("http://xampler.local/blocked-network")


def js_object(value: object) -> Any:
    js_runtime = cast(Any, js)
    return js_runtime.JSON.parse(json.dumps(value))


def keep_callback(callback: Any) -> Any:
    proxy = cast(Any, create_proxy(callback))
    _CALLBACKS.append(proxy)
    return proxy


def index_html() -> str:
    return """<!doctype html>
<title>Xampler Dynamic Workers</title>
<style>body{font:16px system-ui;max-width:760px;margin:2rem auto;line-height:1.5}code,pre{background:#f6f8fa;padding:.2rem .35rem;border-radius:6px}button{font:inherit;padding:.5rem .8rem}</style>
<h1>Dynamic Workers from a Python Worker</h1>
<p>This experimental example uses a <code>worker_loaders</code> binding from a Python Worker to start another Worker isolate at runtime. It also exposes the Python WorkerCode shape Cloudflare documents for Dynamic Python Workers.</p>
<p><button id=run>Run dynamic child</button> <button id=net>Check blocked network</button></p>
<pre id=out>Ready.</pre>
<script>
async function show(path){
  const res = await fetch(path);
  document.querySelector('#out').textContent = await res.text();
}
document.querySelector('#run').onclick = () => show('/run');
document.querySelector('#net').onclick = () => show('/blocked-network');
</script>
"""


def html_response(body: str, *, status: int = 200) -> Response:
    return Response(body, status=status, headers={"content-type": "text/html; charset=utf-8"})


def json_response(data: object, *, status: int = 200) -> Response:
    return Response(
        json.dumps(data, indent=2),
        status=status,
        headers={"content-type": "application/json; charset=utf-8"},
    )
