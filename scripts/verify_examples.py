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


EXAMPLES = {
    "workers-01-hello": Example(
        "workers-01-hello",
        [Check("/", contains="Pythonic Worker")],
    ),
    "r2-01": Example(
        "r2-01",
        [
            Check("/", contains="R2 from Python Workers"),
            Check("/simple/verify.txt", method="PUT", body=b"hello r2", status=201),
            Check("/simple/verify.txt", contains="hello r2"),
            Check(
                "/objects/images/BreakingThe35.jpeg",
                method="PUT",
                body=(Path("r2-01") / "fixtures" / "BreakingThe35.jpeg").read_bytes(),
                headers={"content-type": "image/jpeg"},
                status=201,
            ),
            Check(
                "/objects/images/BreakingThe35.jpeg/stream",
                expected_body=(Path("r2-01") / "fixtures" / "BreakingThe35.jpeg").read_bytes(),
            ),
        ],
    ),
    "kv-02-binding": Example(
        "kv-02-binding",
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
    "fastapi-03-framework": Example(
        "fastapi-03-framework",
        [Check("/", contains="FastAPI"), Check("/items/python", contains="python")],
    ),
    "d1-04-query": Example(
        "d1-04-query",
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
    "assets-06-static-assets": Example(
        "assets-06-static-assets",
        [
            Check("/", contains="Served by Workers Assets"),
            Check("/api/status", contains="Dynamic Python route"),
        ],
    ),
    "durable-objects-07-counter": Example(
        "durable-objects-07-counter",
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
    "scheduled-08-cron": Example(
        "scheduled-08-cron",
        [
            Check("/", contains="scheduled worker is alive"),
            Check("/cdn-cgi/handler/scheduled", status=200),
        ],
    ),
    "queues-16-producer-consumer": Example(
        "queues-16-producer-consumer",
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
            Check("/dev/process-sample", method="POST", contains='"processed": 1'),
        ],
        needs_setup=(
            "Local Wrangler queues accept producer sends; deployed consumers need a real queue."
        ),
    ),
    "workers-ai-09-inference": Example(
        "workers-ai-09-inference",
        [Check("/", contains="response")],
        needs_setup="Requires Workers AI local/runtime support.",
    ),
    "workflows-10-pipeline": Example(
        "workflows-10-pipeline",
        [Check("/", contains="/start")],
        needs_setup="/start requires Workflows runtime support.",
    ),
    "htmlrewriter-11-opengraph": Example(
        "htmlrewriter-11-opengraph",
        [Check("/", contains="og:title")],
    ),
    "images-12-generation": Example(
        "images-12-generation",
        [
            Check(
                "/",
                status=200,
                expected_prefix=b"\x89PNG\r\n\x1a\n",
                response_headers={"content-type": "image/png"},
            )
        ],
    ),
    "service-bindings-13-rpc-py": Example(
        "service-bindings-13-rpc/py",
        [],
        needs_setup=(
            "Run the TS client in service-bindings-13-rpc/ts after "
            "deploying/running the Python service."
        ),
    ),
    "websockets-14-stream-consumer": Example(
        "websockets-14-stream-consumer",
        [Check("/status", contains="connected")],
        needs_setup="Opens an outbound WebSocket to Bluesky Jetstream.",
    ),
    "durable-objects-15-chatroom": Example(
        "durable-objects-15-chatroom",
        [Check("/", contains="Python Workers Chatroom")],
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

    command = ["uv", "run", "pywrangler", "dev", "--port", str(port), "--local"]
    proc = subprocess.Popen(command, cwd=cwd, start_new_session=True)
    try:
        wait_until_ready(port, timeout)
        for check in example.checks:
            run_check(port, check)
            print(f"✓ {check.method} {check.path}")
        return 0
    finally:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)


def wait_until_ready(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read()
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
