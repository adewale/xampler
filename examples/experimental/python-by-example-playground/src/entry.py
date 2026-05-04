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
EXAMPLE_ORDER = [
    "hello-world",
    "values",
    "variables",
    "constants",
    "strings",
    "string-formatting",
    "lists",
    "tuples",
    "dictionaries",
    "sets",
    "slicing",
    "comprehensions",
    "if-else",
    "for-loops",
    "while-loops",
    "break-and-continue",
    "range-and-enumerate",
    "functions",
    "multiple-return-values",
    "variadic-functions",
    "closures",
    "lambdas",
    "classes",
    "methods",
    "inheritance",
    "dataclasses",
    "enums",
    "custom-exceptions",
    "exceptions",
    "type-hints",
    "match",
    "modules",
    "packages",
    "file-paths",
    "directories",
    "reading-files",
    "writing-files",
    "temporary-files",
    "json-example",
    "json-files",
    "regular-expressions",
    "random-numbers",
    "time-example",
    "time-formatting",
    "environment-variables",
    "command-line-arguments",
    "async-basics",
    "async-concurrency",
    "async-queues",
    "http-client",
    "logging-example",
    "recursion",
    "argparse-example",
    "exit",
    "http-server",
    "testing",
]
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


def ordered_examples() -> list[dict[str, str]]:
    rank = {slug: index for index, slug in enumerate(EXAMPLE_ORDER)}
    return sorted(EXAMPLES, key=lambda example: rank.get(example["slug"], len(rank)))


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
                    for example in ordered_examples()
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
MAX_TRACE_EVENTS = 200_000


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
        for example in ordered_examples()
        if example["slug"] not in UNSUPPORTED_SLUGS | {OUTBOUND_EXAMPLE_SLUG}
    ]
    supported_links = example_links(supported)
    unsupported_links = example_links(
        [example for example in ordered_examples() if example["slug"] in UNSUPPORTED_SLUGS]
    )
    outbound = EXAMPLE_BY_SLUG[OUTBOUND_EXAMPLE_SLUG]
    first = supported[0]
    return page(
        "Python by Example Playground",
        f"""
<header class=hero>
<p class=eyebrow>Executable reference</p>
<h1>Python by Example</h1>
<p class=lede>Learn Python through small, editable examples that run in isolated Cloudflare Dynamic Python Workers.</p>
<div class=start-here>
  <div>
    <strong>Start here</strong>
    <span>Begin with <a href=/examples/{html.escape(first['slug'])}>{html.escape(first['title'])}</a>, then follow the list top to bottom.</span>
  </div>
  <a class=buttonish href=/examples/{html.escape(first['slug'])}>Start lesson</a>
</div>
<p class=attrib>Runtime: Cloudflare Python Workers currently use Python 3.13/Pyodide locally; Python 3.14 support depends on Cloudflare upgrading that runtime.</p>
<p class=attrib>Adapted from <a href={SOURCE_URL}>{SOURCE_URL}</a> by {html.escape(SOURCE_AUTHOR)}, licensed under {html.escape(SOURCE_LICENSE)}. See <a href=/attribution>attribution</a>.</p>
</header>
<main class=layout>
<section class=main-column>
<div class=section-head>
  <div>
    <h2>Examples in learning order</h2>
    <p class=muted>Basics → collections → control flow → functions/classes → files/JSON/time → async/networking.</p>
  </div>
  <label class=filter><span>Filter</span><input id=filterExamples placeholder="lists, async, files…" autocomplete=off></label>
</div>
<nav id=examples class=example-list>{supported_links}</nav>
<p id=filterEmpty class="muted hidden">No examples matched that filter.</p>
</section>
<aside class=side-column>
<section class=panel>
<h2>Special capability</h2>
<p><a href=/examples/{OUTBOUND_EXAMPLE_SLUG}>{html.escape(outbound['title'])}</a> demonstrates Dynamic Workers outbound control: run once blocked, then enable the Outbound Worker gateway for <code>example.com</code>.</p>
</section>
<section class="panel unsupported">
<h2>Unsupported in this playground</h2>
<p>Kept for reading, but not part of the happy path because they require process-level CLI, test-runner, or server-socket behavior.</p>
<nav class=compact-list>{unsupported_links}</nav>
</section>
</aside>
</main>
<script>
const filter = document.querySelector('#filterExamples');
const list = document.querySelector('#examples');
const empty = document.querySelector('#filterEmpty');
const original = list.innerHTML;
let examplesCache = null;
function linkFor(example) {{
  const a = document.createElement('a');
  a.href = '/examples/' + example.slug;
  a.dataset.title = (example.title + ' ' + example.summary).toLowerCase();
  a.innerHTML = '<span>' + escapeHtml(example.title) + '</span><small>' + escapeHtml(example.summary) + '</small>';
  return a;
}}
function escapeHtml(value) {{
  return String(value).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}
filter.addEventListener('input', async () => {{
  const q = filter.value.trim().toLowerCase();
  if (!q) {{ list.innerHTML = original; empty.classList.add('hidden'); return; }}
  examplesCache ||= await (await fetch('/api/examples')).json();
  const unsupported = {json.dumps(sorted(UNSUPPORTED_SLUGS))};
  const supported = examplesCache.filter(e => !unsupported.includes(e.slug) && e.slug !== '{OUTBOUND_EXAMPLE_SLUG}');
  const matches = supported.filter(e => (e.title + ' ' + e.summary + ' ' + e.slug).toLowerCase().includes(q));
  list.replaceChildren(...matches.map(linkFor));
  empty.classList.toggle('hidden', matches.length !== 0);
}});
</script>
""",
    )


def example_links(examples: list[dict[str, str]]) -> str:
    return "\n".join(
        f"""<a href=/examples/{html.escape(example['slug'])} data-title=\"{html.escape((example['title'] + ' ' + example['summary']).lower())}\"><span>{html.escape(example['title'])}</span><small>{html.escape(example['summary'])}</small></a>"""
        for example in examples
    )


def example_html(example: dict[str, str]) -> str:
    slug = example["slug"]
    rendered_code = HTTP_CLIENT_CODE if slug == OUTBOUND_EXAMPLE_SLUG else example["code"]
    code = html.escape(rendered_code)
    original_code_json = json.dumps(rendered_code)
    title = html.escape(example["title"])
    summary = html.escape(example["summary"])
    unsupported = slug in UNSUPPORTED_SLUGS
    outbound = slug == OUTBOUND_EXAMPLE_SLUG
    source_url = f"{SOURCE_URL}/blob/main/{example['source_path']}"
    lesson_url = f"{SOURCE_URL}/blob/main/{example['lesson_path']}"
    run_label = "Run anyway" if unsupported else "Run Python"
    return page(
        title,
        f"""
<nav class=crumb><a href=/>← all examples</a></nav>
<header class=lesson-head>
  <p class=eyebrow>{'Unsupported lesson' if unsupported else 'Runnable lesson'}</p>
  <h1>{title}</h1>
  <p class=lede>{summary}</p>
  <p class=attrib>Source: <a href={source_url}>{html.escape(example['source_path'])}</a> · Lesson: <a href={lesson_url}>{html.escape(example['lesson_path'])}</a></p>
</header>
{unsupported_note(unsupported)}
{outbound_note(outbound)}
<div class=limits><strong>Sandbox limits:</strong> CPU budget 50 ms, Python trace budget 200,000 events, outbound network blocked by default, subrequests 0 unless the Outbound Worker checkbox is enabled.</div>
<div class=playground>
  <div class=editor-head><strong>Code</strong><button id=reset type=button class=secondary>Reset</button></div>
  <textarea id=code spellcheck=false>{code}</textarea>
  <div class=actions><button id=run>▶ {run_label}</button>{outbound_checkbox(outbound)}<span id=status class=status>Ready</span></div>
  <div id=resultBanner class="result-banner idle">Ready to run.</div>
  <pre id=out aria-live=polite>Output will appear here without moving the rest of the page.</pre>
  <details id=traceWrap class=trace hidden><summary>Raw traceback / stderr</summary><pre id=trace></pre></details>
</div>
<script>
const ORIGINAL_CODE = {original_code_json};
const code = document.querySelector('#code');
const out = document.querySelector('#out');
const trace = document.querySelector('#trace');
const traceWrap = document.querySelector('#traceWrap');
const status = document.querySelector('#status');
const banner = document.querySelector('#resultBanner');
const outbound = document.querySelector('#allow-outbound');
function setBanner(kind, text) {{
  banner.className = 'result-banner ' + kind;
  banner.textContent = text;
}}
document.querySelector('#reset').onclick = () => {{
  code.value = ORIGINAL_CODE;
  status.textContent = 'Ready';
  setBanner('idle', 'Reset to the original lesson code.');
  out.textContent = 'Output will appear here without moving the rest of the page.';
  trace.textContent = '';
  traceWrap.classList.add('hidden');
}};
document.querySelector('#run').onclick = async () => {{
  status.textContent = 'Running…';
  setBanner('running', 'Running in a Dynamic Python Worker isolate…');
  out.textContent = '';
  trace.textContent = '';
  traceWrap.classList.add('hidden');
  try {{
    const res = await fetch('/api/run', {{
      method: 'POST',
      headers: {{'content-type': 'application/json'}},
      body: JSON.stringify({{code: code.value, allowOutbound: Boolean(outbound && outbound.checked)}})
    }});
    const data = await res.json();
    status.textContent = data.ok ? 'OK' : (data.error_type || 'Error');
    if (data.ok) {{
      setBanner('success', 'Run completed successfully.');
      out.textContent = data.stdout || '(no stdout)';
    }} else {{
      const friendly = data.friendly_error || 'The example raised an error.';
      const kind = data.error_type === 'sandbox_limit' ? 'warning' : 'error';
      setBanner(kind, friendly);
      out.textContent = data.stdout || '(no stdout before the error)';
    }}
    if (data.stderr) {{
      trace.textContent = data.stderr;
      traceWrap.classList.remove('hidden');
    }}
  }} catch (err) {{
    status.textContent = 'Network error';
    setBanner('error', 'The playground request failed before the example could run.');
    out.textContent = String(err);
  }}
}};
</script>
""",
    )


def unsupported_note(enabled: bool) -> str:
    if not enabled:
        return ""
    return """<div class=notice><strong>Unsupported in this playground.</strong> This lesson is useful to read, but the Run button is intentionally labeled “Run anyway” because it relies on process-exit, socket-server, command-line, or test-runner behavior that browser Worker isolates do not model well.</div>"""


def outbound_note(enabled: bool) -> str:
    if not enabled:
        return ""
    return """<div class=notice><strong>Outbound Worker experiment.</strong><ol><li>Run with the checkbox off: <code>globalOutbound = null</code> blocks network access.</li><li>Enable the checkbox and run again: the parent attaches an <code>ExampleOutbound</code> gateway that only allows <code>example.com</code>.</li></ol></div>"""


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
*{{box-sizing:border-box}}body{{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1120px;margin:2rem auto;padding:0 1rem;color:#17202a;background:#fff}}
a{{color:#0b66c3}}.muted,.attrib,small{{color:#536471}}.hidden{{display:none!important}}.eyebrow{{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;font-weight:700;margin:0 0 .25rem}}
h1{{font-size:clamp(2rem,5vw,3rem);line-height:1.05;margin:.2rem 0 .7rem;letter-spacing:-.03em}}h2{{margin:0 0 .6rem;font-size:1.15rem}}.lede{{font-size:1.1rem;max-width:72ch;color:#334155}}
.hero,.lesson-head{{border-bottom:1px solid #d0d7de;margin-bottom:1.5rem;padding-bottom:1.25rem}}.layout{{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:2rem;align-items:start}}.main-column,.side-column{{min-width:0}}.side-column{{position:sticky;top:1rem}}
.start-here{{display:flex;justify-content:space-between;gap:1rem;align-items:center;border:1px solid #d0d7de;border-radius:14px;background:#f8fafc;padding:1rem;margin:1rem 0}}.start-here strong,.start-here span{{display:block}}.buttonish{{display:inline-block;text-decoration:none;background:#0b66c3;color:white;border-radius:8px;padding:.55rem .8rem;white-space:nowrap}}
.section-head{{display:flex;justify-content:space-between;gap:1rem;align-items:end;margin-bottom:1rem}}.filter{{display:grid;gap:.25rem;min-width:220px}}input{{font:inherit;border:1px solid #d0d7de;border-radius:8px;padding:.5rem .65rem;min-width:0}}
.example-list{{columns:2 260px;column-gap:1.75rem}}.example-list a,.compact-list a{{display:block;break-inside:avoid;text-decoration:none;color:#0b66c3;padding:.25rem 0;overflow-wrap:anywhere}}.example-list a span,.compact-list a span{{display:block;font-weight:600}}.example-list a small,.compact-list a small{{display:block;color:#6b7280;font-size:.82rem;line-height:1.25;margin-bottom:.45rem}}
.panel,.notice,.limits{{border:1px solid #d0d7de;border-radius:12px;padding:1rem;background:#f8fafc;margin-bottom:1rem;overflow-wrap:anywhere}}.unsupported{{background:#fff7ed;border-color:#fed7aa}}.limits{{background:#eff6ff;border-color:#bfdbfe;color:#1e3a8a}}
.crumb{{margin-bottom:1rem}}.playground{{border:1px solid #d0d7de;border-radius:12px;overflow:hidden;margin-top:1rem}}.editor-head{{display:flex;justify-content:space-between;align-items:center;padding:.7rem 1rem;background:#f8fafc;border-bottom:1px solid #d0d7de}}textarea{{box-sizing:border-box;width:100%;min-height:360px;max-height:48vh;border:0;border-bottom:1px solid #d0d7de;padding:1rem;font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;resize:vertical}}
.actions{{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;padding:.75rem 1rem;background:#f6f8fa;border-bottom:1px solid #d0d7de}}button{{font:inherit;padding:.5rem .8rem;border-radius:8px;border:1px solid #0b66c3;background:#0b66c3;color:white;cursor:pointer}}button.secondary{{background:white;color:#0b66c3}}.status{{min-width:4rem;color:#536471}}.check{{display:inline-flex;gap:.45rem;align-items:center}}
.result-banner{{padding:.75rem 1rem;border-bottom:1px solid #d0d7de;font-weight:600}}.result-banner.idle{{background:#f8fafc;color:#536471}}.result-banner.running{{background:#eff6ff;color:#1e3a8a}}.result-banner.success{{background:#dcfce7;color:#14532d}}.result-banner.warning{{background:#fef3c7;color:#92400e}}.result-banner.error{{background:#fee2e2;color:#991b1b}}
pre{{margin:0;padding:1rem;background:#0d1117;color:#e6edf3;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere}}#out{{min-height:10rem;max-height:40vh}}.trace{{border-top:1px solid #d0d7de;background:#f8fafc}}.trace summary{{cursor:pointer;padding:.65rem 1rem}}.trace pre{{max-height:18rem}}code{{background:#f6f8fa;padding:.15rem .3rem;border-radius:5px}}
@media(max-width:820px){{body{{margin:1rem auto}}.layout,.section-head,.start-here{{display:block}}.side-column{{position:static}}.example-list{{columns:1}}.filter{{margin-top:1rem}}.buttonish{{margin-top:.75rem}}}}
</style>
{body}
"""


def html_response(body: str, *, status: int = 200) -> Response:
    return Response(body, status=status, headers={"content-type": "text/html; charset=utf-8"})


def json_response(data: object, *, status: int = 200) -> Response:
    return Response(json.dumps(data), status=status, headers={"content-type": "application/json; charset=utf-8"})
