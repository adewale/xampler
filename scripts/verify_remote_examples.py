#!/usr/bin/env python3
"""Env-gated remote verifiers for examples that use real Cloudflare resources.

These checks are separate from scripts/verify_examples.py because they can use
remote bindings, account APIs, deployed Workers, and paid products. Nothing runs
unless XAMPLER_RUN_REMOTE=1 and the profile-specific enable flag are set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import textwrap
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".xampler-remote-state.json"


@dataclass(frozen=True)
class RemoteCheck:
    path: str
    contains: str | None = None
    method: str = "GET"
    body: bytes | None = None
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    attempts: int = 1
    retry_delay: float = 2.0


@dataclass(frozen=True)
class RemoteProfile:
    name: str
    description: str
    enable_env: str
    required_env: tuple[str, ...]
    verifier: Callable[[RemoteProfile, int, float], None]
    example_path: str | None = None
    checks: tuple[RemoteCheck, ...] = ()
    ready_path: str = "/"
    remote_bindings: bool = False
    dev_vars: Mapping[str, str] = field(default_factory=dict)


def account_id_from_wrangler() -> str | None:
    try:
        proc = subprocess.run(
            ["npx", "--yes", "wrangler", "whoami"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError:
        return None
    matches = re.findall(r"[0-9a-f]{32}", proc.stdout)
    return matches[0] if matches else None


def env_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    if name == "CLOUDFLARE_ACCOUNT_ID":
        return account_id_from_wrangler()
    if name == "XAMPLER_R2_SQL_BUCKET":
        return load_state().get("r2-sql", {}).get("bucket") or "xampler-r2-sql"
    if name == "XAMPLER_R2_DATA_CATALOG_URI":
        return load_state().get("r2-data-catalog", {}).get("catalog_uri")
    return None


def env_present(name: str) -> bool:
    return env_value(name) is not None


def load_state() -> dict[str, dict[str, str]]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def state_url(profile: RemoteProfile) -> str | None:
    return load_state().get(profile.name, {}).get("url")


def missing_config(profile: RemoteProfile) -> list[str]:
    missing: list[str] = []
    if os.environ.get("XAMPLER_RUN_REMOTE") != "1":
        missing.append("XAMPLER_RUN_REMOTE=1")
    if os.environ.get(profile.enable_env) != "1":
        missing.append(f"{profile.enable_env}=1")
    for name in profile.required_env:
        if env_present(name):
            continue
        if name.startswith("XAMPLER_REMOTE_") and name.endswith("_URL") and state_url(profile):
            continue
        missing.append(name)
    return missing


@contextmanager
def temporary_dev_vars(example_dir: Path, values: Mapping[str, str]):
    """Write .dev.vars for local Worker dev, restoring any existing file afterwards."""

    if not values:
        yield
        return

    path = example_dir / ".dev.vars"
    previous = path.read_text() if path.exists() else None
    content = "".join(
        f"{key}={shell_quote(value)}\n"
        for key, source in values.items()
        if (value := env_value(source)) is not None
    )
    try:
        path.write_text(content)
        yield
    finally:
        if previous is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(previous)


def shell_quote(value: str) -> str:
    # .dev.vars supports dotenv-style quoted values. Escape only what we emit.
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def run_worker_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    if profile.example_path is None:
        raise ValueError(f"profile {profile.name} has no example_path")
    cwd = ROOT / profile.example_path
    command = ["uv", "run", "pywrangler", "dev", "--port", str(port)]
    command.append("--remote" if profile.remote_bindings else "--local")
    with temporary_dev_vars(cwd, profile.dev_vars):
        proc = subprocess.Popen(command, cwd=cwd, start_new_session=True)
        try:
            wait_until_ready(port, timeout, profile.ready_path)
            base_url = f"http://127.0.0.1:{port}"
            for check in profile.checks:
                run_http_check(base_url, check)
        finally:
            terminate_process_group(proc)


def deployed_base_url(profile: RemoteProfile) -> str:
    url_env = f"XAMPLER_REMOTE_{profile.name.upper().replace('-', '_')}_URL"
    base_url = (os.environ.get(url_env) or state_url(profile) or "").rstrip("/")
    if not base_url:
        raise AssertionError(f"{profile.name}: no deployed URL configured or prepared")
    return base_url


def run_deployed_url_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    del port, timeout
    base_url = deployed_base_url(profile)
    for check in profile.checks:
        run_http_check(base_url, check)


def run_queues_dlq_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    del port
    base_url = deployed_base_url(profile)
    run_http_check(base_url, RemoteCheck("/dev/remote-reset", method="POST"))
    run_http_check(
        base_url,
        RemoteCheck(
            "/jobs",
            method="POST",
            body=b'{"kind":"fail","payload":{"source":"remote-dlq-verifier"}}',
            headers=json_headers,
            status=202,
            contains="remote-dlq-verifier",
        ),
    )
    deadline = time.time() + timeout
    last_body = ""
    while time.time() < deadline:
        request = urllib.request.Request(
            f"{base_url}/dev/remote-status",
            headers={"user-agent": "xampler-remote-verifier/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            last_body = response.read().decode("utf-8", errors="replace")
        data = json.loads(last_body)
        if int(data.get("dead_lettered", 0)) >= 1:
            print("✓ remote Queue DLQ observed")
            return
        time.sleep(5)
    raise AssertionError(f"Queue DLQ message was not observed before timeout: {last_body}")


def run_websocket_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    del port
    base_url = deployed_base_url(profile)
    ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://") + "/room/demo"
    script = f"""
const a = new WebSocket({ws_url!r});
const b = new WebSocket({ws_url!r});
const timeout = setTimeout(
  () => {{ console.error('websocket timeout'); process.exit(1); }},
  {int(timeout * 1000)}
);
b.onmessage = (event) => {{
  if (String(event.data).includes('remote broadcast verifier')) {{
    clearTimeout(timeout);
    a.close();
    b.close();
    console.log('remote broadcast received');
    process.exit(0);
  }}
}};
let opened = 0;
function maybeSend() {{
  opened += 1;
  if (opened === 2) {{
    a.send(JSON.stringify({{ username: 'Ada', text: 'remote broadcast verifier' }}));
  }}
}}
a.onopen = maybeSend;
b.onopen = maybeSend;
a.onerror = b.onerror = (error) => {{ console.error(error); process.exit(1); }};
"""
    subprocess.run(["node", "-e", script], check=True)
    print("✓ remote WebSocket broadcast verifier")


def wait_until_ready(port: int, timeout: float, path: str) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
                if response.status < 500:
                    return
        except urllib.error.HTTPError as error:
            if error.code < 500:
                return
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"remote verifier worker did not become ready on port {port}")


def run_http_check(base_url: str, check: RemoteCheck) -> None:
    last_error: AssertionError | None = None
    for attempt in range(1, check.attempts + 1):
        headers = {"user-agent": "xampler-remote-verifier/1.0", **check.headers}
        request = urllib.request.Request(
            f"{base_url}{check.path}",
            data=check.body,
            method=check.method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                status = response.status
                body_bytes = response.read()
                body = body_bytes.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            status = error.code
            body = error.read().decode("utf-8", errors="replace")
        if status != check.status:
            last_error = AssertionError(
                f"{check.path}: expected {check.status}, got {status}: {body}"
            )
        elif check.contains is not None and check.contains not in body:
            last_error = AssertionError(f"{check.path}: expected {check.contains!r} in {body!r}")
        else:
            print(f"✓ remote {check.method} {check.path}")
            return
        if attempt < check.attempts:
            time.sleep(check.retry_delay)
    if last_error is not None:
        raise last_error


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


def worker_profile(
    name: str,
    description: str,
    *,
    example_path: str,
    checks: tuple[RemoteCheck, ...],
    required_env: tuple[str, ...] = ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
    ready_path: str = "/",
    remote_bindings: bool = False,
    dev_vars: Mapping[str, str] | None = None,
) -> RemoteProfile:
    env_name = name.upper().replace("-", "_")
    return RemoteProfile(
        name=name,
        description=description,
        enable_env=f"XAMPLER_REMOTE_{env_name}",
        required_env=required_env,
        verifier=run_worker_profile,
        example_path=example_path,
        checks=checks,
        ready_path=ready_path,
        remote_bindings=remote_bindings,
        dev_vars=dev_vars or {},
    )


def deployed_profile(name: str, description: str, *checks: RemoteCheck) -> RemoteProfile:
    env_name = name.upper().replace("-", "_")
    return RemoteProfile(
        name=name,
        description=description,
        enable_env=f"XAMPLER_REMOTE_{env_name}",
        required_env=(f"XAMPLER_REMOTE_{env_name}_URL",),
        verifier=run_deployed_url_profile,
        checks=checks,
    )


json_headers = {"content-type": "application/json"}
vectorize_basis = [1, *([0] * 31)]
vectorize_upsert_body = json.dumps(
    {"id": "remote-doc-1", "values": vectorize_basis, "metadata": {"source": "remote"}}
).encode()
vectorize_query_body = json.dumps(
    {"values": vectorize_basis, "top_k": 1, "return_metadata": "all"}
).encode()

PROFILES: dict[str, RemoteProfile] = {
    "workers-ai": deployed_profile(
        "workers-ai",
        "Calls a deployed Worker with the real Workers AI binding.",
        RemoteCheck("/", contains="text"),
    ),
    "vectorize": deployed_profile(
        "vectorize",
        "Uses a deployed Worker with the real Vectorize binding.",
        RemoteCheck("/describe"),
        RemoteCheck(
            "/upsert",
            method="POST",
            body=vectorize_upsert_body,
            headers=json_headers,
        ),
        RemoteCheck(
            "/query",
            method="POST",
            body=vectorize_query_body,
            headers=json_headers,
            contains="remote-doc-1",
            attempts=12,
            retry_delay=5.0,
        ),
    ),
    "browser-rendering": deployed_profile(
        "browser-rendering",
        "Calls a deployed Worker that uses the real Browser Rendering REST API.",
        RemoteCheck("/?url=https%3A%2F%2Fexample.com"),
        RemoteCheck("/content?url=https%3A%2F%2Fexample.com", contains="Example Domain"),
        RemoteCheck("/pdf?url=https%3A%2F%2Fexample.com", contains="%PDF"),
        RemoteCheck("/scrape?url=https%3A%2F%2Fexample.com", contains="Example Domain"),
    ),
    "r2-sql": deployed_profile(
        "r2-sql",
        "Calls a deployed Worker that uses the real R2 SQL REST API.",
        RemoteCheck(
            "/",
            method="POST",
            body=b'{"sql":"SHOW TABLES IN xampler"}',
            headers=json_headers,
            contains="gutenberg_smoke",
        ),
        RemoteCheck(
            "/",
            method="POST",
            body=b'{"sql":"SELECT * FROM xampler.gutenberg_smoke LIMIT 1"}',
            headers=json_headers,
            contains="gutenberg_smoke",
        ),
    ),
    "ai-gateway": worker_profile(
        "ai-gateway",
        "Calls the real AI Gateway endpoint from the Worker.",
        example_path="examples/ai-agents/ai-gateway-chat",
        required_env=(
            "CLOUDFLARE_ACCOUNT_ID",
            "CLOUDFLARE_API_TOKEN",
            "XAMPLER_AI_GATEWAY_ID",
            "OPENAI_API_KEY",
        ),
        ready_path="/demo",
        checks=(RemoteCheck("/", contains="choices"),),
        dev_vars={
            "ACCOUNT_ID": "CLOUDFLARE_ACCOUNT_ID",
            "GATEWAY_ID": "XAMPLER_AI_GATEWAY_ID",
            "OPENAI_API_KEY": "OPENAI_API_KEY",
        },
    ),
    "r2-data-catalog": deployed_profile(
        "r2-data-catalog",
        "Calls a deployed Worker that uses a real R2 Data Catalog/Iceberg endpoint.",
        RemoteCheck("/tables/xampler", contains="gutenberg_smoke"),
        RemoteCheck(
            "/lifecycle/xampler_verify/temp_table",
            method="POST",
            contains="lifecycle_complete",
        ),
    ),
    "hyperdrive": deployed_profile(
        "hyperdrive",
        "Calls a deployed real Hyperdrive query route.",
        RemoteCheck("/query"),
    ),
    "images": deployed_profile(
        "images",
        "Calls a deployed real Cloudflare Images route.",
        RemoteCheck("/"),
    ),
    "analytics-engine": deployed_profile(
        "analytics-engine",
        "Calls a deployed real Analytics Engine route.",
        RemoteCheck("/"),
    ),
    "queues-dlq": RemoteProfile(
        name="queues-dlq",
        description="Calls deployed Queue producer/consumer/DLQ verification routes.",
        enable_env="XAMPLER_REMOTE_QUEUES_DLQ",
        required_env=("XAMPLER_REMOTE_QUEUES_DLQ_URL",),
        verifier=run_queues_dlq_profile,
    ),
    "service-bindings": deployed_profile(
        "service-bindings",
        "Calls deployed cross-worker Service Binding routes.",
        RemoteCheck("/?code=print('called%20from%20remote')", contains="called from remote"),
    ),
    "websockets": RemoteProfile(
        name="websockets",
        description="Calls deployed WebSocket verification route.",
        enable_env="XAMPLER_REMOTE_WEBSOCKETS",
        required_env=("XAMPLER_REMOTE_WEBSOCKETS_URL",),
        verifier=run_websocket_profile,
    ),
}


def print_profile_help(profile: RemoteProfile) -> None:
    print(profile.description)
    print("Required:")
    print("  XAMPLER_RUN_REMOTE=1")
    print(f"  {profile.enable_env}=1")
    for name in profile.required_env:
        print(f"  {name}=...")


EXAMPLE_USAGE = """
Examples:
  uv run python scripts/verify_remote_examples.py --list
  XAMPLER_RUN_REMOTE=1 XAMPLER_REMOTE_WORKERS_AI=1 \
    CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... \
    uv run python scripts/verify_remote_examples.py workers-ai
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(EXAMPLE_USAGE),
    )
    parser.add_argument("profile", nargs="?", choices=sorted(PROFILES))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--show-env", action="store_true")
    parser.add_argument("--port", type=int, default=9850)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()

    if args.list:
        for name, profile in sorted(PROFILES.items()):
            print(f"{name}: {profile.description}")
        return 0
    if args.profile is None:
        parser.error("profile required unless --list is used")

    profile = PROFILES[args.profile]
    if args.show_env:
        print_profile_help(profile)
        return 0

    missing = missing_config(profile)
    if missing:
        print(f"SKIP {profile.name}: set {', '.join(missing)} to run this paid/remote check")
        return 0
    profile.verifier(profile, args.port, args.timeout)
    print(f"✓ remote profile {profile.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
