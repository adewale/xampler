# ruff: noqa: E501
from __future__ import annotations

import inspect
import json
from typing import Any, cast
from urllib.parse import urlparse

import js  # type: ignore[import-not-found]
import workers as workers_sdk  # type: ignore[import-not-found]
import workers._workers as workers_impl  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]
from workers import Response, WorkerEntrypoint, python_from_rpc  # type: ignore[import-not-found]

from xampler.experimental.dynamic_workers import python_fetch_worker, stable_worker_id

COMPATIBILITY_DATE = "2026-05-01"
_CALLBACKS: list[Any] = []

PYTHON_CHILD_SOURCE = '''from __future__ import annotations

from typing import Any
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        message = getattr(self.env, "MESSAGE", "hello from a dynamic Python Worker")
        return Response(message, headers={"x-dynamic-worker": "python"})
'''

PYTHON_NETWORK_TEST_SOURCE = '''from __future__ import annotations

from typing import Any
from workers import Response, WorkerEntrypoint, fetch


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        try:
            await fetch("https://example.com")
        except Exception as exc:
            return Response("blocked: " + exc.__class__.__name__)
        return Response("unexpected network access", status=500)
'''


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        path = urlparse(str(request.url)).path
        if path == "/":
            return html_response(index_html())
        if path == "/run":
            return await run_dynamic_child(self.env.LOADER, request)
        if path == "/forward":
            return await forward_to_one_off_dynamic_child(self.env.LOADER, request)
        if path == "/blocked-network":
            return await run_network_check(self.env.LOADER, request)
        if path == "/worker-code":
            code = python_fetch_worker(PYTHON_CHILD_SOURCE, compatibility_date=COMPATIBILITY_DATE)
            return json_response(code.to_raw())
        return Response("not found", status=404)


async def run_dynamic_child(loader: Any, request: Any) -> Response:
    _ = request
    code = python_fetch_worker(PYTHON_CHILD_SOURCE, compatibility_date=COMPATIBILITY_DATE)
    raw = with_workers_sdk(code.to_raw())
    raw["env"] = {"MESSAGE": "hello from a Dynamic Python Worker loaded by Python"}
    worker_id = stable_worker_id("xampler-python-child", json.dumps(raw, sort_keys=True))

    def load_code() -> Any:
        return js_object(raw)

    worker = loader.get(worker_id, keep_callback(load_code))
    return await worker.getEntrypoint().fetch("http://xampler.local/run")


async def forward_to_one_off_dynamic_child(loader: Any, request: Any) -> Response:
    code = python_fetch_worker(PYTHON_CHILD_SOURCE, compatibility_date=COMPATIBILITY_DATE)
    raw = with_workers_sdk(code.to_raw())
    raw["env"] = {"MESSAGE": "hello via LOADER.load one-off Python Dynamic Worker"}
    worker = loader.load(js_object(raw))
    entrypoint = worker.getEntrypoint()
    child_response = cast(Any, python_from_rpc(await entrypoint.fetch(request.js_object)))
    return Response(await child_response.text(), status=int(child_response.status))


async def run_network_check(loader: Any, request: Any) -> Response:
    _ = request
    code = python_fetch_worker(PYTHON_NETWORK_TEST_SOURCE, compatibility_date=COMPATIBILITY_DATE)
    raw = with_workers_sdk(code.to_raw())

    def load_code() -> Any:
        return js_object(raw)

    worker = loader.get(
        stable_worker_id("xampler-network-check", json.dumps(raw, sort_keys=True)),
        keep_callback(load_code),
    )
    return await worker.getEntrypoint().fetch("http://xampler.local/blocked-network")


def with_workers_sdk(raw: dict[str, Any]) -> dict[str, Any]:
    modules = cast(dict[str, Any], raw["modules"])
    modules["workers/__init__.py"] = inspect.getsource(workers_sdk)
    modules["workers/_workers.py"] = inspect.getsource(workers_impl)
    return raw


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
<p>It includes both cache-friendly <code>LOADER.get(id, callback)</code> and one-off <code>LOADER.load(workerCode)</code> flows, following the shape shown in <a href=https://github.com/irvinebroque/dynamic-workers-python>irvinebroque/dynamic-workers-python</a>.</p>
<p><button id=run>Run cached dynamic child</button> <button id=forward>Forward through LOADER.load</button> <button id=net>Check blocked network</button></p>
<pre id=out>Ready.</pre>
<script>
async function show(path){
  const res = await fetch(path);
  document.querySelector('#out').textContent = await res.text();
}
document.querySelector('#run').onclick = () => show('/run');
document.querySelector('#forward').onclick = () => show('/forward');
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
