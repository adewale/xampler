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
UNSUPPORTED_SLUGS = {"argparse-example", "exit", "http-server", "testing"}
OUTBOUND_EXAMPLE_SLUG = "http-client"
HTTP_CLIENT_CODE = '''from workers import fetch

# This example is special in the playground: outbound network is controlled
# by a checkbox that toggles Dynamic Workers globalOutbound.
response = await fetch("https://example.com")
body = await response.text()
print(response.status)
print(body[:120] + "...")
'''
EXAMPLE_BY_SLUG = {example["slug"]: example for example in EXAMPLES}
_CALLBACKS: list[Any] = []


class ExampleOutbound(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        url = urlparse(str(request.url))
        if url.hostname not in {"example.com", "www.example.com"}:
            return Response("Outbound Worker blocked " + str(request.url), status=403)
        return await cast(Any, js).fetch(str(request.url))


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
            allow_outbound = bool(payload.get("allowOutbound", False))
            ctx = cast(Any, self).ctx
            outbound_fetcher: Any | None = (
                ctx.exports.ExampleOutbound(js_object({})) if allow_outbound else None
            )
            return await run_code(
                self.env.LOADER,
                code,
                allow_outbound=allow_outbound,
                outbound_fetcher=outbound_fetcher,
            )
        if path == "/attribution":
            return html_response(attribution_html())
        return Response("not found", status=404)


async def run_code(
    loader: Any,
    code: str,
    *,
    allow_outbound: bool = False,
    outbound_fetcher: Any | None = None,
) -> Response:
    child_source = runner_source(code)
    worker_code = DynamicWorkerCode(
        compatibility_date=COMPATIBILITY_DATE,
        compatibility_flags=["python_workers", "disable_python_external_sdk"],
        main_module="runner.py",
        modules={"runner.py": child_source},
        global_outbound=None,
        limits=DynamicWorkerLimits(cpu_ms=50, subrequests=1 if allow_outbound else 0),
    )
    raw = with_workers_sdk(worker_code.to_raw())

    def load_code() -> Any:
        obj = js_object(raw)
        if outbound_fetcher is not None:
            obj.globalOutbound = outbound_fetcher
        return obj

    worker = loader.get(stable_worker_id("python-by-example-runner", worker_code), keep_callback(load_code))
    return await worker.getEntrypoint().fetch("http://xampler.local/run")


def runner_source(user_code: str) -> str:
    return f'''from __future__ import annotations

import ast
import contextlib
import inspect
import io
import json
import sys
import traceback
from typing import Any
from workers import Response, WorkerEntrypoint

USER_CODE = {user_code!r}
MAX_TRACE_EVENTS = 20_000


class SandboxLimitExceeded(RuntimeError):
    pass


def make_trace_limiter():
    events = 0

    def trace(frame: Any, event: str, arg: Any) -> Any:
        nonlocal events
        if event in {"line", "call", "jump"}:
            events += 1
            if events > MAX_TRACE_EVENTS:
                raise SandboxLimitExceeded(
                    "Execution stopped: sandbox instruction limit exceeded. "
                    "This usually means the example entered an infinite loop "
                    "or did too much work for the playground."
                )
        return trace

    return trace


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            namespace = {{"__name__": "__main__"}}
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                compiled = compile(
                    USER_CODE,
                    "<user_code>",
                    "exec",
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                )
                sys.settrace(make_trace_limiter())
                try:
                    result = eval(compiled, namespace, namespace)
                    if inspect.isawaitable(result):
                        await result
                finally:
                    sys.settrace(None)
            payload = {{"ok": True, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}}
        except SandboxLimitExceeded as exc:
            payload = {{
                "ok": False,
                "error_type": "sandbox_limit",
                "friendly_error": str(exc),
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue() + str(exc) + "\\n",
            }}
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 0
            payload = {{
                "ok": code == 0,
                "error_type": "system_exit",
                "friendly_error": f"The example called sys.exit({{code!r}}). Process exits are shown explicitly in the playground.",
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue() if code == 0 else stderr.getvalue() + traceback.format_exc(),
            }}
        except BaseException as exc:
            payload = {{
                "ok": False,
                "error_type": exc.__class__.__name__,
                "friendly_error": friendly_error(exc),
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue() + traceback.format_exc(),
            }}
        return Response(json.dumps(payload), headers={{"content-type": "application/json; charset=utf-8"}})


def friendly_error(exc: BaseException) -> str:
    text = str(exc)
    if "not permitted to access the internet" in text:
        return "Network access is blocked for this run. Enable the Outbound Worker checkbox on the HTTP Client example to allow example.com."
    if "Host is unreachable" in text:
        return "Network access is unavailable in this sandboxed Worker run."
    return f"{{exc.__class__.__name__}}: {{text}}"
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
    supported = [
        example
        for example in EXAMPLES
        if example["slug"] not in UNSUPPORTED_SLUGS | {OUTBOUND_EXAMPLE_SLUG}
    ]
    supported_links = example_links(supported)
    unsupported_links = example_links(
        [example for example in EXAMPLES if example["slug"] in UNSUPPORTED_SLUGS]
    )
    outbound = EXAMPLE_BY_SLUG[OUTBOUND_EXAMPLE_SLUG]
    return page(
        "Python by Example Playground",
        f"""
<header class=hero>
<h1>Python by Example</h1>
<p>Executable Python examples in the style of <a href=https://gobyexample.com/>Go by Example</a>, running inside Cloudflare Dynamic Python Worker isolates.</p>
<p class=attrib>Adapted from <a href={SOURCE_URL}>{SOURCE_URL}</a> by {html.escape(SOURCE_AUTHOR)}, licensed under {html.escape(SOURCE_LICENSE)}. See <a href=/attribution>attribution</a>.</p>
</header>
<main class=layout>
<section>
<h2>Examples</h2>
<nav class=example-list>{supported_links}</nav>
</section>
<aside>
<section class=panel>
<h2>Outbound Worker example</h2>
<p><a href=/examples/{OUTBOUND_EXAMPLE_SLUG}>{html.escape(outbound['title'])}</a> is a special Dynamic Workers networking demo with a checkbox that enables or disables calls to <code>example.com</code>.</p>
</section>
<section class="panel unsupported">
<h2>Unsupported in this playground</h2>
<p>These examples intentionally exit the process, bind server sockets, or need command-line/test-runner behavior that is not a good fit for this Worker isolate.</p>
<nav class=example-list>{unsupported_links}</nav>
</section>
</aside>
</main>
""",
    )


def example_links(examples: list[dict[str, str]]) -> str:
    return "\n".join(
        f"""<a href=/examples/{html.escape(example['slug'])}><span>{html.escape(example['title'])}</span><small>{html.escape(example['summary'])}</small></a>"""
        for example in examples
    )


def example_html(example: dict[str, str]) -> str:
    slug = example["slug"]
    rendered_code = HTTP_CLIENT_CODE if slug == OUTBOUND_EXAMPLE_SLUG else example["code"]
    code = html.escape(rendered_code)
    title = html.escape(example["title"])
    summary = html.escape(example["summary"])
    unsupported = slug in UNSUPPORTED_SLUGS
    outbound = slug == OUTBOUND_EXAMPLE_SLUG
    source_url = f"{SOURCE_URL}/blob/main/{example['source_path']}"
    lesson_url = f"{SOURCE_URL}/blob/main/{example['lesson_path']}"
    return page(
        title,
        f"""
<p><a href=/>← all examples</a></p>
<h1>{title}</h1>
<p>{summary}</p>
{unsupported_note(unsupported)}
{outbound_note(outbound)}
<p class=attrib>Source: <a href={source_url}>{html.escape(example['source_path'])}</a> · Lesson: <a href={lesson_url}>{html.escape(example['lesson_path'])}</a></p>
<div class=limits><strong>Sandbox limits:</strong> CPU budget 50 ms, Python trace budget 20,000 events, outbound network blocked by default, subrequests 0 unless the Outbound Worker checkbox is enabled.</div>
<div class=playground>
<textarea id=code spellcheck=false>{code}</textarea>
<div class=actions><button id=run>▶ Run Python</button>{outbound_checkbox(outbound)}<span id=status></span></div>
<pre id=out>Click Run Python to execute this example in a Dynamic Python Worker isolate.</pre>
</div>
<script>
const code = document.querySelector('#code');
const out = document.querySelector('#out');
const status = document.querySelector('#status');
const outbound = document.querySelector('#allow-outbound');
document.querySelector('#run').onclick = async () => {{
  status.textContent = 'running…';
  out.textContent = '';
  try {{
    const res = await fetch('/api/run', {{
      method: 'POST',
      headers: {{'content-type': 'application/json'}},
      body: JSON.stringify({{code: code.value, allowOutbound: Boolean(outbound && outbound.checked)}})
    }});
    const data = await res.json();
    status.textContent = data.ok ? 'ok' : (data.error_type || 'error');
    const friendly = data.friendly_error ? data.friendly_error + '\\n\\n' : '';
    out.textContent = friendly + (data.stdout || '') + (data.stderr || '');
  }} catch (err) {{
    status.textContent = 'error';
    out.textContent = String(err);
  }}
}};
</script>
""",
    )


def unsupported_note(enabled: bool) -> str:
    if not enabled:
        return ""
    return """<div class=notice><strong>Unsupported.</strong> This lesson is kept for reading, but it relies on process-exit, socket-server, command-line, or test-runner behavior that this browser Worker playground does not model well.</div>"""


def outbound_note(enabled: bool) -> str:
    if not enabled:
        return ""
    return """<div class=notice><strong>Outbound Worker demo.</strong> Dynamic Workers can run with <code>globalOutbound = null</code> to block network access, or with an Outbound Worker/fetcher to allow and mediate outbound <code>fetch</code>. Use the checkbox below to attach outbound fetch capability for this isolate so it can call <code>https://example.com</code>.</div>"""


def outbound_checkbox(enabled: bool) -> str:
    if not enabled:
        return ""
    return """<label class=check><input id=allow-outbound type=checkbox> Enable Outbound Worker access to example.com</label>"""


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
*{{box-sizing:border-box}}body{{font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1120px;margin:2rem auto;padding:0 1rem;color:#17202a}}
a{{color:#0b66c3}}.attrib,small{{color:#536471}}.hero{{border-bottom:1px solid #d0d7de;margin-bottom:1.25rem;padding-bottom:1rem}}
.layout{{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:2rem;align-items:start}}h1{{font-size:2.4rem;margin:.2rem 0}}h2{{margin:1rem 0 .6rem}}
.example-list{{columns:2 260px;column-gap:1.5rem}}.example-list a{{display:block;break-inside:avoid;text-decoration:none;color:#0b66c3;padding:.22rem 0}}
.example-list a span{{display:block}}.example-list a small{{display:block;color:#6b7280;font-size:.82rem;line-height:1.25;margin-bottom:.35rem}}
.panel,.notice,.limits{{border:1px solid #d0d7de;border-radius:12px;padding:1rem;background:#f8fafc;margin-bottom:1rem}}.unsupported{{background:#fff7ed;border-color:#fed7aa}}
.limits{{background:#eff6ff;border-color:#bfdbfe;color:#1e3a8a}}
.playground{{border:1px solid #d0d7de;border-radius:12px;overflow:hidden}}textarea{{box-sizing:border-box;width:100%;min-height:380px;border:0;border-bottom:1px solid #d0d7de;padding:1rem;font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}}
.actions{{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;padding:.75rem 1rem;background:#f6f8fa;border-bottom:1px solid #d0d7de}}button{{font:inherit;padding:.45rem .8rem;border-radius:8px;border:1px solid #0b66c3;background:#0b66c3;color:white;cursor:pointer}}
.check{{display:inline-flex;gap:.45rem;align-items:center}}pre{{margin:0;padding:1rem;min-height:120px;background:#0d1117;color:#e6edf3;overflow:auto;white-space:pre-wrap}}code{{background:#f6f8fa;padding:.15rem .3rem;border-radius:5px}}
@media(max-width:820px){{.layout{{display:block}}.example-list{{columns:1}}}}
</style>
{body}
"""


def html_response(body: str, *, status: int = 200) -> Response:
    return Response(body, status=status, headers={"content-type": "text/html; charset=utf-8"})


def json_response(data: object, *, status: int = 200) -> Response:
    return Response(json.dumps(data), status=status, headers={"content-type": "application/json; charset=utf-8"})
