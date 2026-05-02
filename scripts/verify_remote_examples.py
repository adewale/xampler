#!/usr/bin/env python3
"""Env-gated remote verifiers for examples that may use real Cloudflare resources.

These checks are intentionally separate from scripts/verify_examples.py. They can
consume real account resources and may cost money. Nothing runs unless
XAMPLER_RUN_REMOTE=1 and the profile-specific enable flag are set.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Callable
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
    example_path: str | None = None
    checks: tuple[RemoteCheck, ...] = ()
    ready_path: str = "/"
    verifier: Callable[[int, float], None] | None = None


def env_present(name: str) -> bool:
    value = os.environ.get(name)
    return value is not None and value != ""


def require_remote_enabled(profile: RemoteProfile) -> list[str]:
    missing: list[str] = []
    if os.environ.get("XAMPLER_RUN_REMOTE") != "1":
        missing.append("XAMPLER_RUN_REMOTE=1")
    if os.environ.get(profile.enable_env) != "1":
        missing.append(f"{profile.enable_env}=1")
    missing.extend(name for name in profile.required_env if not env_present(name))
    return missing


def verify_workers_ai(port: int, timeout: float) -> None:
    run_worker_profile(
        RemoteProfile(
            name="workers-ai",
            description="Workers AI binding remote check via local Wrangler dev.",
            enable_env="XAMPLER_REMOTE_WORKERS_AI",
            required_env=("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
            example_path="examples/ai-agents/workers-ai-inference",
            ready_path="/demo",
            checks=(RemoteCheck("/", contains="text"),),
        ),
        port,
        timeout,
    )


def run_deployed_url_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    del port, timeout
    url_env = f"XAMPLER_REMOTE_{profile.name.upper().replace('-', '_')}_URL"
    base_url = os.environ[url_env].rstrip("/")
    for check in profile.checks:
        run_http_check(base_url, check)


def run_worker_profile(profile: RemoteProfile, port: int, timeout: float) -> None:
    if profile.example_path is None:
        raise ValueError(f"profile {profile.name} has no example_path")
    proc = subprocess.Popen(
        ["uv", "run", "pywrangler", "dev", "--port", str(port), "--local"],
        cwd=ROOT / profile.example_path,
        start_new_session=True,
    )
    try:
        wait_until_ready(port, timeout, profile.ready_path)
        base_url = f"http://127.0.0.1:{port}"
        for check in profile.checks:
            run_http_check(base_url, check)
    finally:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)


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
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        status = error.code
        body = error.read().decode("utf-8", errors="replace")
    if status != check.status:
        raise AssertionError(f"{check.path}: expected {check.status}, got {status}: {body}")
    if check.contains is not None and check.contains not in body:
        raise AssertionError(f"{check.path}: expected {check.contains!r} in {body!r}")
    print(f"✓ remote {check.method} {check.path}")


def deployed_profile(name: str, description: str, *checks: RemoteCheck) -> RemoteProfile:
    env_name = name.upper().replace("-", "_")
    return RemoteProfile(
        name=name,
        description=description,
        enable_env=f"XAMPLER_REMOTE_{env_name}",
        required_env=(f"XAMPLER_REMOTE_{env_name}_URL",),
        checks=checks,
        verifier=run_deployed_url_profile,
    )


PROFILES: dict[str, RemoteProfile] = {
    "workers-ai": RemoteProfile(
        name="workers-ai",
        description="Calls the real Workers AI binding route. May incur Workers AI usage.",
        enable_env="XAMPLER_REMOTE_WORKERS_AI",
        required_env=("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
        verifier=verify_workers_ai,
    ),
    "ai-gateway": deployed_profile(
        "ai-gateway", "Calls a deployed real AI Gateway route.", RemoteCheck("/", contains="choice")
    ),
    "vectorize": deployed_profile(
        "vectorize", "Calls deployed real Vectorize routes.", RemoteCheck("/describe")
    ),
    "browser-rendering": deployed_profile(
        "browser-rendering", "Calls a deployed real Browser Rendering route.", RemoteCheck("/")
    ),
    "hyperdrive": deployed_profile(
        "hyperdrive", "Calls a deployed real Hyperdrive query route.", RemoteCheck("/query")
    ),
    "r2-sql": deployed_profile("r2-sql", "Calls a deployed real R2 SQL route.", RemoteCheck("/")),
    "r2-data-catalog": deployed_profile(
        "r2-data-catalog", "Calls a deployed real R2 Data Catalog route.", RemoteCheck("/")
    ),
    "images": deployed_profile(
        "images",
        "Calls a deployed real Cloudflare Images route.",
        RemoteCheck("/"),
    ),
    "analytics-engine": deployed_profile(
        "analytics-engine", "Calls a deployed real Analytics Engine route.", RemoteCheck("/")
    ),
    "queues-dlq": deployed_profile(
        "queues-dlq",
        "Calls deployed Queue producer/consumer/DLQ verification routes.",
        RemoteCheck("/"),
    ),
    "service-bindings": deployed_profile(
        "service-bindings", "Calls deployed cross-worker Service Binding routes.", RemoteCheck("/")
    ),
    "websockets": deployed_profile(
        "websockets", "Calls deployed WebSocket verification HTTP route.", RemoteCheck("/")
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", nargs="?", choices=sorted(PROFILES))
    parser.add_argument("--list", action="store_true")
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
    missing = require_remote_enabled(profile)
    if missing:
        print(f"SKIP {profile.name}: set {', '.join(missing)} to run this paid/remote check")
        return 0
    if profile.verifier is None:
        raise AssertionError(f"profile {profile.name} has no verifier")
    profile.verifier(args.port, args.timeout)
    print(f"✓ remote profile {profile.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
