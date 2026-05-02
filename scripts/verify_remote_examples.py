#!/usr/bin/env python3
"""Env-gated remote verifiers for examples that use real Cloudflare resources.

These checks are separate from scripts/verify_examples.py because they can use
remote bindings, account APIs, deployed Workers, and paid products. Nothing runs
unless XAMPLER_RUN_REMOTE=1 and the profile-specific enable flag are set.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RemoteCheck:
    path: str
    contains: str | None = None
    method: str = "GET"
    body: bytes | None = None
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)


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


def env_present(name: str) -> bool:
    value = os.environ.get(name)
    return value is not None and value != ""


def missing_config(profile: RemoteProfile) -> list[str]:
    missing: list[str] = []
    if os.environ.get("XAMPLER_RUN_REMOTE") != "1":
        missing.append("XAMPLER_RUN_REMOTE=1")
    if os.environ.get(profile.enable_env) != "1":
        missing.append(f"{profile.enable_env}=1")
    missing.extend(name for name in profile.required_env if not env_present(name))
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
        f"{key}={shell_quote(os.environ[source])}\n" for key, source in values.items()
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


def run_deployed_url_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    del port, timeout
    url_env = f"XAMPLER_REMOTE_{profile.name.upper().replace('-', '_')}_URL"
    base_url = os.environ[url_env].rstrip("/")
    for check in profile.checks:
        run_http_check(base_url, check)


def wait_until_ready(port: int, timeout: float, path: str) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"remote verifier worker did not become ready on port {port}")


def run_http_check(base_url: str, check: RemoteCheck) -> None:
    request = urllib.request.Request(
        f"{base_url}{check.path}",
        data=check.body,
        method=check.method,
        headers=check.headers,
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
        raise AssertionError(f"{check.path}: expected {check.status}, got {status}: {body}")
    if check.contains is not None and check.contains not in body:
        raise AssertionError(f"{check.path}: expected {check.contains!r} in {body!r}")
    print(f"✓ remote {check.method} {check.path}")


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

PROFILES: dict[str, RemoteProfile] = {
    "workers-ai": worker_profile(
        "workers-ai",
        "Calls the real Workers AI binding route through Wrangler remote dev.",
        example_path="examples/ai-agents/workers-ai-inference",
        ready_path="/demo",
        remote_bindings=True,
        checks=(RemoteCheck("/", contains="text"),),
    ),
    "vectorize": worker_profile(
        "vectorize",
        "Uses the real Vectorize binding through Wrangler remote dev.",
        example_path="examples/ai-agents/vectorize-search",
        ready_path="/demo",
        remote_bindings=True,
        checks=(
            RemoteCheck("/describe"),
            RemoteCheck(
                "/upsert",
                method="POST",
                body=b'{"id":"remote-doc-1","values":[1,0,0],"metadata":{"source":"remote"}}',
                headers=json_headers,
            ),
            RemoteCheck(
                "/query",
                method="POST",
                body=b'{"values":[1,0,0],"top_k":1,"return_metadata":"all"}',
                headers=json_headers,
                contains="remote-doc-1",
            ),
        ),
    ),
    "browser-rendering": worker_profile(
        "browser-rendering",
        "Calls the real Browser Rendering REST API from the Worker.",
        example_path="examples/network-edge/browser-rendering-screenshot",
        ready_path="/demo",
        checks=(RemoteCheck("/?url=https%3A%2F%2Fexample.com"),),
        dev_vars={"ACCOUNT_ID": "CLOUDFLARE_ACCOUNT_ID", "CF_API_TOKEN": "CLOUDFLARE_API_TOKEN"},
    ),
    "r2-sql": worker_profile(
        "r2-sql",
        "Calls the real R2 SQL REST API from the Worker.",
        example_path="examples/storage-data/r2-sql",
        checks=(
            RemoteCheck(
                "/",
                method="POST",
                body=b'{"sql":"SHOW DATABASES"}',
                headers=json_headers,
            ),
        ),
        dev_vars={"ACCOUNT_ID": "CLOUDFLARE_ACCOUNT_ID", "CF_API_TOKEN": "CLOUDFLARE_API_TOKEN"},
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
    "r2-data-catalog": worker_profile(
        "r2-data-catalog",
        "Calls a real R2 Data Catalog/Iceberg REST endpoint from the Worker.",
        example_path="examples/storage-data/r2-data-catalog",
        required_env=("XAMPLER_R2_DATA_CATALOG_URI", "XAMPLER_R2_DATA_CATALOG_TOKEN"),
        ready_path="/demo",
        checks=(RemoteCheck("/"),),
        dev_vars={
            "CATALOG_URI": "XAMPLER_R2_DATA_CATALOG_URI",
            "CATALOG_TOKEN": "XAMPLER_R2_DATA_CATALOG_TOKEN",
        },
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
    "queues-dlq": deployed_profile(
        "queues-dlq",
        "Calls deployed Queue producer/consumer/DLQ verification routes.",
        RemoteCheck("/"),
    ),
    "service-bindings": deployed_profile(
        "service-bindings",
        "Calls deployed cross-worker Service Binding routes.",
        RemoteCheck("/"),
    ),
    "websockets": deployed_profile(
        "websockets",
        "Calls deployed WebSocket verification route.",
        RemoteCheck("/"),
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
