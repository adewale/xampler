# ruff: noqa: E501
from __future__ import annotations

import html
import inspect
import json
from typing import Any, cast
from urllib.parse import unquote, urlparse

import js  # type: ignore[import-not-found]
import workers as workers_sdk  # type: ignore[import-not-found]
import workers._workers as workers_impl  # type: ignore[import-not-found]
from examples_data import EXAMPLES, SOURCE_AUTHOR, SOURCE_LICENSE, SOURCE_URL
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.experimental.dynamic_workers import (
    DynamicWorkerCode,
    DynamicWorkerLimits,
    stable_worker_id,
)

COMPATIBILITY_DATE = "2026-05-01"
EXAMPLE_BY_SLUG = {example["slug"]: example for example in EXAMPLES}
_CALLBACKS: list[Any] = []


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        parsed = urlparse(str(request.url))
        path = parsed.path
        if path == "/":
            return html_response(index_html())
        if path == "/api/examples":
            return json_response(
                [
                    {
                        "slug": example["slug"],
                        "title": example["title"],
                        "summary": example["summary"],
                        "source_path": example["source_path"],
                        "lesson_path": example["lesson_path"],
                    }
                    for example in EXAMPLES
                ]
            )
        if path.startswith("/examples/"):
            slug = unquote(path.removeprefix("/examples/")).strip("/")
            example = EXAMPLE_BY_SLUG.get(slug)
            if example is None:
                return Response("not found", status=404)
            return html_response(example_html(example))
        if path == "/api/run" and request.method == "POST":
            payload = await request.json()
            code = str(payload.get("code", ""))[:20_000]
            return await run_code(self.env.LOADER, code)
        if path == "/attribution":
            return html_response(attribution_html())
        return Response("not found", status=404)


async def run_code(loader: Any, code: str) -> Response:
    child_source = runner_source(code)
    worker_code = DynamicWorkerCode(
        compatibility_date=COMPATIBILITY_DATE,
        compatibility_flags=["python_workers", "disable_python_external_sdk"],
        main_module="runner.py",
        modules={"runner.py": child_source},
        global_outbound=None,
        limits=DynamicWorkerLimits(cpu_ms=50, subrequests=0),
    )
    raw = with_workers_sdk(worker_code.to_raw())

    def load_code() -> Any:
        return js_object(raw)

    worker = loader.get(stable_worker_id("python-by-example-runner", worker_code), keep_callback(load_code))
    return await worker.getEntrypoint().fetch("http://xampler.local/run")


def runner_source(user_code: str) -> str:
    return f'''from __future__ import annotations

import contextlib
import io
import json
import traceback
from typing import Any
from workers import Response, WorkerEntrypoint

USER_CODE = {user_code!r}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            namespace = {{"__name__": "__main__"}}
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(USER_CODE, namespace, namespace)
            payload = {{"ok": True, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}}
        except BaseException:
            payload = {{"ok": False, "stdout": stdout.getvalue(), "stderr": stderr.getvalue() + traceback.format_exc()}}
        return Response(json.dumps(payload), headers={{"content-type": "application/json; charset=utf-8"}})
'''


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
    cards = "\n".join(
        f"""<a class=card href=/examples/{html.escape(example['slug'])}>
<h2>{html.escape(example['title'])}</h2>
<p>{html.escape(example['summary'])}</p>
<small>{html.escape(example['source_path'])}</small>
</a>"""
        for example in EXAMPLES
    )
    return page(
        "Python by Example Playground",
        f"""
<header>
<h1>Python by Example Playground</h1>
<p>A Cloudflare Python Workers playground inspired by <a href=https://gobyexample.com/>Go by Example</a>. Each example includes a play button that runs editable Python code immediately in a Dynamic Python Worker isolate.</p>
<p class=attrib>Examples adapted from <a href={SOURCE_URL}>{SOURCE_URL}</a> by {html.escape(SOURCE_AUTHOR)}, licensed under {html.escape(SOURCE_LICENSE)}. See <a href=/attribution>attribution</a>.</p>
</header>
<nav class=grid>{cards}</nav>
""",
    )


def example_html(example: dict[str, str]) -> str:
    code = html.escape(example["code"])
    title = html.escape(example["title"])
    summary = html.escape(example["summary"])
    source_url = f"{SOURCE_URL}/blob/main/{example['source_path']}"
    lesson_url = f"{SOURCE_URL}/blob/main/{example['lesson_path']}"
    return page(
        title,
        f"""
<p><a href=/>← all examples</a></p>
<h1>{title}</h1>
<p>{summary}</p>
<p class=attrib>Source: <a href={source_url}>{html.escape(example['source_path'])}</a> · Lesson: <a href={lesson_url}>{html.escape(example['lesson_path'])}</a></p>
<div class=playground>
<textarea id=code spellcheck=false>{code}</textarea>
<div class=actions><button id=run>▶ Run Python</button><span id=status></span></div>
<pre id=out>Click Run Python to execute this example in a Dynamic Python Worker isolate.</pre>
</div>
<script>
const code = document.querySelector('#code');
const out = document.querySelector('#out');
const status = document.querySelector('#status');
document.querySelector('#run').onclick = async () => {{
  status.textContent = 'running…';
  out.textContent = '';
  try {{
    const res = await fetch('/api/run', {{
      method: 'POST',
      headers: {{'content-type': 'application/json'}},
      body: JSON.stringify({{code: code.value}})
    }});
    const data = await res.json();
    status.textContent = data.ok ? 'ok' : 'error';
    out.textContent = (data.stdout || '') + (data.stderr || '');
  }} catch (err) {{
    status.textContent = 'error';
    out.textContent = String(err);
  }}
}};
</script>
""",
    )


def attribution_html() -> str:
    return page(
        "Attribution",
        f"""
<p><a href=/>← all examples</a></p>
<h1>Attribution</h1>
<p>This playground vendors example source from <a href={SOURCE_URL}>{SOURCE_URL}</a>.</p>
<ul>
<li>Original project: Python by Example</li>
<li>Author/copyright line from upstream license: Dariush Abbasi (<a href=https://github.com/dariubs>https://github.com/dariubs</a>)</li>
<li>Repository owner: pycollege</li>
<li>License: {html.escape(SOURCE_LICENSE)}</li>
</ul>
<p>The transformation here adds the Cloudflare Dynamic Python Workers playground UI. The original lesson/source links remain attached to each example.</p>
""",
    )


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body{{font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1120px;margin:2rem auto;padding:0 1rem;color:#17202a}}
a{{color:#0b66c3}}.attrib{{color:#536471}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}}
.card{{display:block;text-decoration:none;color:inherit;border:1px solid #d0d7de;border-radius:12px;padding:1rem;background:#fff;box-shadow:0 1px 2px #0001}}
.card:hover{{border-color:#0b66c3}}.card h2{{font-size:1.1rem;margin:.1rem 0}}.card p{{color:#536471}}small{{color:#6b7280}}
.playground{{border:1px solid #d0d7de;border-radius:12px;overflow:hidden}}textarea{{box-sizing:border-box;width:100%;min-height:380px;border:0;border-bottom:1px solid #d0d7de;padding:1rem;font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}}
.actions{{display:flex;gap:1rem;align-items:center;padding:.75rem 1rem;background:#f6f8fa;border-bottom:1px solid #d0d7de}}button{{font:inherit;padding:.45rem .8rem;border-radius:8px;border:1px solid #0b66c3;background:#0b66c3;color:white;cursor:pointer}}
pre{{margin:0;padding:1rem;min-height:120px;background:#0d1117;color:#e6edf3;overflow:auto;white-space:pre-wrap}}code{{background:#f6f8fa;padding:.15rem .3rem;border-radius:5px}}
</style>
{body}
"""


def html_response(body: str, *, status: int = 200) -> Response:
    return Response(body, status=status, headers={"content-type": "text/html; charset=utf-8"})


def json_response(data: object, *, status: int = 200) -> Response:
    return Response(json.dumps(data), status=status, headers={"content-type": "application/json; charset=utf-8"})
