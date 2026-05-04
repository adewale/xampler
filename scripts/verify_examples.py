#!/usr/bin/env python3
"""Run local smoke checks for examples.

This script is intentionally boring: it runs any local setup commands, starts
`uv run pywrangler dev`, waits for the local server, performs HTTP checks, and
shuts Wrangler down. The examples should be verifiable the same way the official
Cloudflare examples are verifiable: run a Worker and make requests against it.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Check:
    path: str
    method: str = "GET"
    body: bytes | None = None
    expected_body: bytes | None = None
    expected_prefix: bytes | None = None
    contains: str | None = None
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Example:
    name: str
    checks: list[Check]
    needs_setup: str | None = None
    setup_commands: list[list[str]] = field(default_factory=list)
    dev_command: list[str] | None = None
    ready_path: str = "/"


R2_FIXTURE = Path("examples/storage-data/r2-object-storage") / "fixtures" / "BreakingThe35.jpeg"


EXAMPLES = {
    "examples/start/hello-worker": Example(
        "examples/start/hello-worker",
        [Check("/", contains="Pythonic Worker")],
    ),
    "examples/storage-data/r2-object-storage": Example(
        "examples/storage-data/r2-object-storage",
        [
            Check("/", contains="R2 from Python Workers"),
            Check("/simple/verify.txt", method="PUT", body=b"hello r2", status=201),
            Check("/simple/verify.txt", contains="hello r2"),
            Check(
                "/objects/images/BreakingThe35.jpeg",
                method="PUT",
                body=R2_FIXTURE.read_bytes(),
                headers={"content-type": "image/jpeg"},
                status=201,
            ),
            Check(
                "/objects/images/BreakingThe35.jpeg/stream",
                expected_body=R2_FIXTURE.read_bytes(),
            ),
        ],
    ),
    "examples/storage-data/kv-namespace": Example(
        "examples/storage-data/kv-namespace",
        [
            Check("/text/verify", method="PUT", body=b"hello kv", status=201),
            Check("/text/verify", contains="hello kv"),
            Check(
                "/json/profile",
                method="PUT",
                body=b'{"name":"Ada","language":"Python"}',
                headers={"content-type": "application/json"},
                status=201,
            ),
            Check("/json/profile", contains="Python"),
            Check("/keys", contains="verify"),
            Check("/keys/verify", method="DELETE", contains="deleted"),
            Check("/text/verify", status=404, contains="not found"),
        ],
        needs_setup="Wrangler accepts placeholder KV ids for local dev; replace id before deploy.",
    ),
    "examples/start/fastapi-worker": Example(
        "examples/start/fastapi-worker",
        [Check("/", contains="FastAPI"), Check("/items/python", contains="python")],
    ),
    "examples/storage-data/d1-database": Example(
        "examples/storage-data/d1-database",
        [
            Check("/", contains="PEP 20"),
            Check("/by-author?author=PEP%2020", contains="Readability"),
            Check("/explain?author=PEP%2020", contains="idx_quotes_author"),
        ],
        needs_setup=(
            "The verifier initializes local D1 with db_init.sql before starting the Worker."
        ),
        setup_commands=[
            [
                "uv",
                "run",
                "pywrangler",
                "d1",
                "execute",
                "xampler-d1",
                "--local",
                "--file",
                "db_init.sql",
            ]
        ],
    ),
    "examples/start/static-assets": Example(
        "examples/start/static-assets",
        [
            Check("/", contains="Served by Workers Assets"),
            Check("/api/status", contains="Dynamic Python route"),
        ],
    ),
    "examples/state-events/durable-object-counter": Example(
        "examples/state-events/durable-object-counter",
        [
            Check("/demo/reset", contains="0"),
            Check("/other/reset", contains="0"),
            Check("/demo/increment", contains="1"),
            Check("/demo/increment", contains="2"),
            Check("/other/increment", contains="1"),
            Check("/demo", contains="2"),
            Check("/other", contains="1"),
        ],
    ),
    "examples/state-events/cron-trigger": Example(
        "examples/state-events/cron-trigger",
        [
            Check("/", contains="scheduled worker is alive"),
            Check("/cdn-cgi/handler/scheduled", status=200),
        ],
    ),
    "examples/state-events/queues-producer-consumer": Example(
        "examples/state-events/queues-producer-consumer",
        [
            Check("/", contains="POST JSON"),
            Check(
                "/jobs",
                method="POST",
                body=b'{"kind":"resize","payload":{"image":"r2://demo/input.jpg"}}',
                headers={"content-type": "application/json"},
                status=202,
                contains="resize",
            ),
            Check("/dev/process-sample", method="POST", contains='"processed"'),
            Check("/dev/process-failing", method="POST", contains='"dead_lettered"'),
        ],
        needs_setup=(
            "Local Wrangler queues accept producer sends; deployed consumers need a real queue."
        ),
    ),
    "examples/ai-agents/workers-ai-inference": Example(
        "examples/ai-agents/workers-ai-inference",
        [Check("/demo", contains="Workers AI response")],
        needs_setup=(
            "/ uses the real Workers AI binding; /demo is deterministic for local verification."
        ),
        ready_path="/demo",
    ),
    "examples/state-events/workflows-pipeline": Example(
        "examples/state-events/workflows-pipeline",
        [
            Check("/demo/start", contains="demo-instance"),
            Check("/demo/status/demo-instance", contains="complete"),
            Check("/timeline/demo-instance", contains="fetch input"),
        ],
        needs_setup="/start uses real Workflows; /demo/* is deterministic for local verification.",
        setup_commands=[
            [
                "uv",
                "run",
                "pywrangler",
                "d1",
                "execute",
                "xampler-workflows",
                "--local",
                "--file",
                "db_init.sql",
            ]
        ],
    ),
    "examples/network-edge/htmlrewriter-opengraph": Example(
        "examples/network-edge/htmlrewriter-opengraph",
        [Check("/", contains="og:title"), Check("/extract", contains="canonical_url")],
    ),
    "examples/ai-agents/vectorize-search": Example(
        "examples/ai-agents/vectorize-search",
        [Check("/demo", contains="doc-1")],
        needs_setup="Real /upsert and /query use Vectorize; /demo is deterministic locally.",
    ),
    "examples/streaming/binary-response": Example(
        "examples/streaming/binary-response",
        [
            Check(
                "/",
                status=200,
                expected_prefix=b"\x89PNG\r\n\x1a\n",
                response_headers={"content-type": "image/png"},
            )
        ],
    ),
    "examples/network-edge/service-bindings-rpc/py": Example(
        "examples/network-edge/service-bindings-rpc/py",
        [Check("/", contains="service binding rpc")],
        needs_setup="Python provider is locally verified; TS client shows cross-worker binding.",
    ),
    "examples/network-edge/service-bindings-rpc/ts": Example(
        "examples/network-edge/service-bindings-rpc/ts",
        [Check("/?code=print('called%20from%20ts')", contains="called from ts")],
        needs_setup="Starts TS client and Python provider; TS invokes Python via Service Binding.",
    ),
    "examples/network-edge/outbound-websocket-consumer": Example(
        "examples/network-edge/outbound-websocket-consumer",
        [Check("/demo/status", contains="demo-websocket-stream")],
        needs_setup="/status opens Bluesky Jetstream; /demo/status is deterministic locally.",
    ),
    "examples/state-events/durable-object-chatroom": Example(
        "examples/state-events/durable-object-chatroom",
        [
            Check("/", contains="Python Workers Chatroom"),
            Check(
                "/room/demo/dev/send",
                method="POST",
                body=b'{"username":"Ada","text":"hello room"}',
                headers={"content-type": "application/json"},
                contains="hello room",
            ),
            Check("/room/demo/dev/history", contains="hello room"),
            Check("/room/demo/dev/replay", contains="hello room"),
            Check("/room/demo/dev/export", contains="transcript"),
        ],
    ),
    "examples/network-edge/browser-rendering-screenshot": Example(
        "examples/network-edge/browser-rendering-screenshot",
        [
            Check("/demo?url=https://example.com", contains="demo-browser-rendering"),
            Check("/report", contains="Browser Rendering Report"),
            Check("/demo/report-verifier", contains="pdf_longer_than_title"),
        ],
        needs_setup="/ uses real Browser Rendering REST API; /demo is deterministic locally.",
        ready_path="/demo",
    ),
    "examples/network-edge/email-worker-router": Example(
        "examples/network-edge/email-worker-router",
        [
            Check("/", contains="forward to archive@example.net"),
            Check("/fixtures/email/allow", contains='"action": "allow"'),
            Check("/fixtures/email/reject", contains='"action": "reject"'),
            Check("/fixtures/email/forward", contains='"action": "forward"'),
            Check("/fixtures/email/annotate", contains='"action": "annotate"'),
        ],
        needs_setup=(
            "Email event routing is deployed-only; HTTP route verifies deterministic policy."
        ),
    ),
    "examples/ai-agents/ai-gateway-chat": Example(
        "examples/ai-agents/ai-gateway-chat",
        [Check("/demo", contains="demo-ai-gateway")],
        needs_setup="/ uses real AI Gateway; /demo verifies gateway-shaped responses locally.",
        ready_path="/demo",
    ),
    "examples/storage-data/r2-data-catalog": Example(
        "examples/storage-data/r2-data-catalog",
        [Check("/demo", contains="hvsc"), Check("/demo/tables/hvsc", contains="tracks")],
        needs_setup=(
            "Real routes use Iceberg REST; /demo verifies catalog-shaped responses locally."
        ),
        ready_path="/demo",
    ),
    "examples/ai-agents/langchain-style-chain": Example(
        "examples/ai-agents/langchain-style-chain",
        [Check("/", contains="LangChain-compatible LCEL demo")],
        needs_setup=(
            "Uses a dependency-light LCEL-style Runnable chain for local Workers verification."
        ),
    ),
    "examples/streaming/gutenberg-stream-composition": Example(
        "examples/streaming/gutenberg-stream-composition",
        [
            Check("/demo", contains="gutenberg-stream-demo"),
            Check("/events", contains="gutenberg.search"),
            Check("/zip-demo", contains="r2-object-body"),
            Check("/fts/ingest", contains='"all_chunks_indexed": true'),
            Check("/fts/search?q=romeo%20juliet", contains='"count"'),
            Check("/fts/verify", contains='"all_queries_return_results": true'),
            Check("/pipeline/ingest-r2-lines", contains='"all_lines_checkpointed": true'),
            Check("/pipeline/status", contains="gutenberg-r2-lines"),
        ],
        needs_setup=(
            "Golden Gutenberg zip is stored in R2; verifier initializes local D1 FTS."
        ),
        setup_commands=[
            [
                "uv",
                "run",
                "pywrangler",
                "d1",
                "execute",
                "xampler-gutenberg",
                "--local",
                "--file",
                "db_init.sql",
            ]
        ],
        ready_path="/demo",
    ),
    "examples/storage-data/hyperdrive-postgres": Example(
        "examples/storage-data/hyperdrive-postgres",
        [
            Check("/demo", contains="demo-hyperdrive"),
            Check("/query", status=501, contains="Hyperdrive"),
        ],
        needs_setup="/query needs a configured Hyperdrive/Postgres client; /demo is local.",
        ready_path="/demo",
    ),
    "examples/ai-agents/agents-sdk-tools": Example(
        "examples/ai-agents/agents-sdk-tools",
        [
            Check("/demo?message=weather%20in%20Lagos", contains="weather.lookup"),
            Check("/demo/transcript", contains="calculator.eval"),
            Check(
                "/agents/demo/run",
                method="POST",
                body=b'{"message":"weather in London"}',
                headers={"content-type": "application/json"},
                contains="London",
            ),
        ],
        needs_setup="Uses deterministic tool calls locally and Durable Objects for agent sessions.",
        ready_path="/demo",
    ),
    "examples/storage-data/r2-sql": Example(
        "examples/storage-data/r2-sql",
        [
            Check(
                "/demo",
                method="POST",
                body=b'{"sql":"SELECT bucket, objects FROM object_inventory"}',
                headers={"content-type": "application/json"},
                contains="LIMIT 100",
            ),
            Check(
                "/demo/explain",
                method="POST",
                body=b'{"sql":"SELECT bucket, objects FROM object_inventory"}',
                headers={"content-type": "application/json"},
                contains="single-table",
            ),
        ],
        needs_setup="Real / calls the R2 SQL API; /demo verifies safe query shaping locally.",
    ),
    "examples/start/pages-functions": Example(
        "examples/start/pages-functions",
        [
            Check("/", contains="Xampler Pages"),
            Check("/api/hello?name=Python", contains="Hello, Python"),
        ],
        needs_setup="Pages Functions are TypeScript today; verifier uses Wrangler Pages dev.",
        dev_command=["uv", "run", "pywrangler", "pages", "dev", "public", "--port"],
    ),
    "examples/full-apps/mini-wiki": Example(
        "examples/full-apps/mini-wiki",
        [
            Check("/", contains="Good wiki loop"),
            Check("/style.css", contains="wiki-layout"),
            Check("/all", contains="Wiki Guide"),
            Check("/wanted", contains="Project Ideas"),
            Check("/wiki/page-links", contains="Home Page"),
            Check("/wiki/home-page/edit", contains="Syntax guide"),
            Check("/wiki/project-ideas", contains="Create page"),
            Check(
                "/dev/render",
                method="POST",
                body=b"body=%23%20Preview%0A%0ASee%20%5B%5BPage%20Links%5D%5D",
                headers={"content-type": "application/x-www-form-urlencoded"},
                contains="/wiki/page-links",
            ),
            Check(
                "/wiki/home-page",
                method="POST",
                body=(
                    b"base_revision=1&title=Home%20Page&body=%23%20Home%20Page%0A%0A"
                    b"Updated%20wiki%20text%20about%20D1Search%20and%20%5B%5BProject%20Ideas%5D%5D."
                    b"&author=Ada&message=update"
                ),
                headers={"content-type": "application/x-www-form-urlencoded"},
                contains="Revision saved.",
            ),
            Check("/wiki/home-page/history", contains="diff-add"),
            Check("/search?q=D1Search", contains="<mark>D1Search</mark>"),
            Check("/search?q=NoSuchPage", contains="Create No Such Page"),
            Check("/dev/cached/wiki/home-page", contains="D1Search"),
            Check("/dev/events", contains="http.request"),
            Check("/export.jsonl", contains='"revision":2'),
        ],
        needs_setup="Initializes local D1; CSS is served by Workers Static Assets.",
        setup_commands=[
            [
                "uv",
                "run",
                "pywrangler",
                "d1",
                "execute",
                "xampler-mini-wiki",
                "--local",
                "--file",
                "db_init.sql",
            ]
        ],
    ),
    "examples/experimental/dynamic-workers-loader": Example(
        "examples/experimental/dynamic-workers-loader",
        [
            Check("/", contains="Dynamic Workers from a Python Worker"),
            Check("/worker-code", contains="worker.py"),
            Check("/run", contains="Dynamic Python Worker loaded by Python"),
            Check("/blocked-network", contains="blocked:"),
        ],
        needs_setup="Dynamic Workers are local-first and beta-gated for deployed usage.",
    ),
    "examples/experimental/python-by-example-playground": Example(
        "examples/experimental/python-by-example-playground",
        [
            Check("/", contains="Unsupported in this playground"),
            Check("/examples/hello-world", contains="Run Python"),
            Check("/examples/http-client", contains="Outbound Worker demo"),
            Check("/api/examples", contains="hello-world"),
            Check(
                "/api/run",
                method="POST",
                body=b'{"code":"print(1 + 2)"}',
                headers={"content-type": "application/json"},
                contains='"stdout": "3\\n"',
            ),
            Check(
                "/api/run",
                method="POST",
                body=(
                    b'{"code":"from workers import fetch\\nresponse = await fetch('
                    b'\\"https://example.com\\")\\nprint(response.status)",'
                    b'"allowOutbound":true}'
                ),
                headers={"content-type": "application/json"},
                contains='"stdout": "200\\n"',
            ),
        ],
        needs_setup="Runs editable snippets in Dynamic Python Worker isolates locally.",
    ),
    "examples/full-apps/hvsc-ai-data-search": Example(
        "examples/full-apps/hvsc-ai-data-search",
        [
            Check("/", contains="HVSC full-catalog search"),
            Check("/ingest-fixture", method="POST", contains="HVSC #84"),
            Check("/search?q=sid", contains="HVSC #84"),
            Check("/tracks?q=jeroen", contains="d1_tracks"),
            Check("/archive/verify", contains='"verified"'),
            Check("/catalog/verify-r2", contains='"exists"'),
            Check("/r2/status", contains='"ready_for_import"'),
            Check("/catalog/ingest-sample", method="POST", contains='"streamed"'),
        ],
        needs_setup=(
            "Initializes local D1 and uses deterministic AI/vector logic over HVSC metadata."
        ),
        setup_commands=[
            [
                "uv",
                "run",
                "pywrangler",
                "d1",
                "execute",
                "xampler-hvsc",
                "--local",
                "--file",
                "db_init.sql",
            ]
        ],
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("example", nargs="?", help="example name, or omit with --list")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()

    if args.list:
        print(json.dumps({name: ex.needs_setup for name, ex in EXAMPLES.items()}, indent=2))
        return 0
    if not args.example or args.example not in EXAMPLES:
        print("Choose one of:", ", ".join(EXAMPLES), file=sys.stderr)
        return 2

    if args.example == "examples/network-edge/service-bindings-rpc/ts":
        return verify_service_binding_rpc(args.port, args.timeout)

    example = EXAMPLES[args.example]
    if example.needs_setup:
        print(f"Note: {example.needs_setup}")
    if not example.checks:
        print("No automated HTTP checks for this example yet.")
        return 0

    return verify(example, args.port, args.timeout)


def verify(example: Example, port: int, timeout: float) -> int:
    cwd = Path(example.name)
    for setup_command in example.setup_commands:
        subprocess.run(setup_command, cwd=cwd, check=True)

    command = example.dev_command or ["uv", "run", "pywrangler", "dev", "--port"]
    command = [*command, str(port)]
    if example.dev_command is None:
        command.append("--local")
    proc = subprocess.Popen(command, cwd=cwd, start_new_session=True)
    try:
        wait_until_ready(port, timeout, example.ready_path)
        for check in example.checks:
            run_check(port, check)
            print(f"✓ {check.method} {check.path}")
        interactive_script_paths = {
            "examples/ai-agents/agents-sdk-tools": ["/"],
            "examples/experimental/python-by-example-playground": ["/examples/hello-world"],
            "examples/full-apps/mini-wiki": ["/wiki/home-page/edit"],
            "examples/state-events/durable-object-chatroom": ["/"],
            "examples/state-events/workflows-pipeline": ["/"],
            "examples/streaming/gutenberg-stream-composition": ["/"],
        }
        if example.name in interactive_script_paths:
            verify_inline_browser_scripts(port, interactive_script_paths[example.name])
        if example.name == "examples/state-events/durable-object-chatroom":
            verify_chatroom_websocket(port)
        if example.name == "examples/full-apps/hvsc-ai-data-search":
            verify_hvsc_degraded_full_catalog_flow(port)
        return 0
    finally:
        terminate_process_group(proc)


def request_text(port: int, check: Check) -> str:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{check.path}",
        data=check.body,
        method=check.method,
        headers=check.headers,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def request_json(port: int, check: Check) -> dict[str, object]:
    body = request_text(port, check)
    data = json.loads(body)
    if not isinstance(data, dict):
        raise AssertionError(f"{check.path}: expected JSON object, got {data!r}")
    return data


def verify_inline_browser_scripts(port: int, paths: list[str]) -> None:
    for path in paths:
        html_body = request_text(port, Check(path))
        scripts: list[str] = []
        search_offset = 0
        while True:
            start = html_body.find("<script", search_offset)
            if start < 0:
                break
            tag_end = html_body.find(">", start)
            if tag_end < 0:
                raise AssertionError(f"{path}: unterminated opening script tag")
            close = html_body.find("</script>", tag_end)
            if close < 0:
                raise AssertionError(f"{path}: unterminated inline script")
            script_tag = html_body[start:tag_end].lower()
            if " src=" not in script_tag and "type=\"application/json\"" not in script_tag:
                scripts.append(html_body[tag_end + 1 : close])
            search_offset = close + len("</script>")
        if not scripts:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as script_file:
            script_file.write("\n".join(scripts))
            script_path = script_file.name
        try:
            subprocess.run(["node", "--check", script_path], check=True)
        finally:
            Path(script_path).unlink(missing_ok=True)
        print(f"✓ {path} inline JavaScript compiles")


def verify_hvsc_degraded_full_catalog_flow(port: int) -> None:
    """Verify the full-catalog browser flow and its setup guidance."""
    verify_inline_browser_scripts(port, ["/"])
    start = request_json(port, Check("/ingest/start", method="POST"))
    if start.get("status") == "error" and "no shards found" in str(start.get("error", "")):
        html_body = request_text(port, Check("/"))
        setup_command = "scripts/hvsc_upload_catalog.py xampler-datasets --local"
        if setup_command not in html_body:
            raise AssertionError("HVSC UI did not explain how to seed full catalog shards")
        print("✓ HVSC missing-shards path gives full-catalog setup guidance")
        return

    if start.get("status") not in {"running", "complete"}:
        raise AssertionError(f"Unexpected HVSC ingest/start state: {start!r}")
    total_shards = int(start.get("total_shards", 0))
    if total_shards <= 0:
        raise AssertionError(f"HVSC full-catalog state has no shards: {start!r}")
    print("✓ HVSC full-catalog shard ingest can start")


def verify_chatroom_websocket(port: int) -> None:
    script = f"""
const a = new WebSocket('ws://127.0.0.1:{port}/room/demo');
const b = new WebSocket('ws://127.0.0.1:{port}/room/demo');
let seen = false;
const timeout = setTimeout(() => {{ console.error('websocket timeout'); process.exit(1); }}, 10000);
b.onmessage = (event) => {{
  if (String(event.data).includes('broadcast verifier')) {{
    seen = true;
    clearTimeout(timeout);
    a.close();
    b.close();
    console.log('broadcast received');
    process.exit(0);
  }}
}};
let opened = 0;
function maybeSend() {{
  opened += 1;
  if (opened === 2) {{
    a.send(JSON.stringify({{ username: 'Ada', text: 'broadcast verifier' }}));
  }}
}}
a.onopen = maybeSend;
b.onopen = maybeSend;
a.onerror = b.onerror = (error) => {{ console.error(error); process.exit(1); }};
"""
    subprocess.run(["node", "-e", script], check=True)
    print("✓ WebSocket broadcast verifier")


def verify_service_binding_rpc(port: int, timeout: float) -> int:
    root = Path("examples/network-edge/service-bindings-rpc")
    py_proc = subprocess.Popen(
        ["uv", "run", "pywrangler", "dev", "--port", str(port), "--local"],
        cwd=root / "py",
        start_new_session=True,
    )
    ts_proc: subprocess.Popen[bytes] | None = None
    try:
        wait_until_ready(port, timeout)
        ts_port = port + 1
        ts_proc = subprocess.Popen(
            ["npx", "--yes", "wrangler", "dev", "--port", str(ts_port), "--local"],
            cwd=root / "ts",
            start_new_session=True,
        )
        wait_until_ready(ts_port, timeout)
        run_check(ts_port, Check("/?code=print('called%20from%20ts')", contains="called from ts"))
        print("✓ TS Worker invoked Python RPC service binding")
        return 0
    finally:
        for proc in (ts_proc, py_proc):
            terminate_process_group(proc)


def terminate_process_group(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            return


def wait_until_ready(port: int, timeout: float, path: str = "/") -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=1).read()
            return
        except urllib.error.HTTPError:
            return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError("wrangler dev did not become ready")


def run_check(port: int, check: Check) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{check.path}",
        data=check.body,
        method=check.method,
        headers=check.headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            response_headers = response.headers
            body_bytes = response.read()
            body = body_bytes.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        response_headers = exc.headers
        body_bytes = exc.read()
        body = body_bytes.decode("utf-8", errors="replace")

    if status != check.status:
        raise AssertionError(f"{check.path}: expected {check.status}, got {status}: {body}")
    if check.contains is not None and check.contains not in body:
        raise AssertionError(f"{check.path}: did not find {check.contains!r} in {body!r}")
    if check.expected_body is not None and body_bytes != check.expected_body:
        raise AssertionError(f"{check.path}: downloaded body did not match expected bytes")
    if check.expected_prefix is not None and not body_bytes.startswith(check.expected_prefix):
        raise AssertionError(f"{check.path}: body did not start with expected bytes")
    for name, expected in check.response_headers.items():
        actual = response_headers.get(name, "")
        if expected.lower() not in actual.lower():
            raise AssertionError(
                f"{check.path}: expected {name} to contain {expected!r}, got {actual!r}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
