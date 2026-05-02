#!/usr/bin/env python3
"""Prepare real Cloudflare resources for env-gated remote example verification.

This script is intentionally separate from local verification because it creates
or deploys remote Cloudflare resources and may incur costs. It uses normal
Wrangler authentication (`npx wrangler login`) wherever possible.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".xampler-remote-state.json"

PROFILE_DESCRIPTIONS: dict[str, str] = {
    "vectorize": "Create the xampler-vectorize index used by the Vectorize example.",
    "queues-dlq": "Create Queues/DLQ and deploy the Queue producer/consumer Worker.",
    "service-bindings": "Deploy Python provider then TypeScript consumer for Service Bindings RPC.",
    "websockets": "Deploy the Durable Object chatroom Worker for real WebSocket checks.",
    "browser-rendering": "Preflight Browser Rendering REST credentials.",
    "r2-sql": "Create R2 bucket/catalog prerequisites for R2 SQL.",
    "r2-data-catalog": "Create R2 bucket/catalog prerequisites for R2 Data Catalog.",
}


def run(
    command: list[str], *, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(command), f"(cwd={cwd})" if cwd else "")
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def run_print(
    command: list[str], *, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    proc = run(command, cwd=cwd, check=check)
    if proc.stdout:
        print(proc.stdout.rstrip())
    return proc


def require_remote_prepare(profile: str) -> None:
    if (
        os.environ.get("XAMPLER_RUN_REMOTE") != "1"
        or os.environ.get("XAMPLER_PREPARE_REMOTE") != "1"
    ):
        raise SystemExit(
            f"Refusing to prepare {profile}: set XAMPLER_RUN_REMOTE=1 and "
            "XAMPLER_PREPARE_REMOTE=1 because this creates/deploys remote resources."
        )


def load_state() -> dict[str, dict[str, str]]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, dict[str, str]]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def record_url(profile: str, url: str) -> None:
    state = load_state()
    state.setdefault(profile, {})["url"] = url.rstrip("/")
    save_state(state)
    print(f"Recorded {profile} URL: {url.rstrip('/')}")


def parse_deploy_url(output: str) -> str:
    urls = re.findall(r"https://[^\s]+\.workers\.dev", output)
    if not urls:
        raise RuntimeError("could not find workers.dev URL in deploy output")
    return urls[-1].rstrip(".,")


def wrangler_json(command: list[str], *, cwd: Path | None = None) -> object | None:
    proc = run(command + ["--json"], cwd=cwd, check=False)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def prepare_vectorize() -> None:
    require_remote_prepare("vectorize")
    existing = wrangler_json(["npx", "--yes", "wrangler", "vectorize", "get", "xampler-vectorize"])
    if existing is None:
        run_print(
            [
                "npx",
                "--yes",
                "wrangler",
                "vectorize",
                "create",
                "xampler-vectorize",
                "--dimensions=32",
                "--metric=cosine",
            ]
        )
        existing = wrangler_json(
            ["npx", "--yes", "wrangler", "vectorize", "get", "xampler-vectorize"]
        )
    print("Vectorize index ready: xampler-vectorize")
    if existing is not None:
        print(json.dumps(existing, indent=2, sort_keys=True))
    url = deploy_pyworker("examples/ai-agents/vectorize-search")
    record_url("vectorize", url)


def queue_exists(name: str) -> bool:
    return run(["npx", "--yes", "wrangler", "queues", "info", name], check=False).returncode == 0


def ensure_queue(name: str) -> None:
    if queue_exists(name):
        print(f"Queue exists: {name}")
        return
    run_print(["npx", "--yes", "wrangler", "queues", "create", name])


def deploy_pyworker(example: str) -> str:
    proc = run_print(["uv", "run", "pywrangler", "deploy"], cwd=ROOT / example)
    return parse_deploy_url(proc.stdout)


def deploy_wrangler(example: str) -> str:
    proc = run_print(["npx", "--yes", "wrangler", "deploy"], cwd=ROOT / example)
    return parse_deploy_url(proc.stdout)


def prepare_queues_dlq() -> None:
    require_remote_prepare("queues-dlq")
    ensure_queue("xampler-jobs")
    ensure_queue("xampler-jobs-dlq")
    url = deploy_pyworker("examples/state-events/queues-producer-consumer")
    record_url("queues-dlq", url)


def prepare_service_bindings() -> None:
    require_remote_prepare("service-bindings")
    deploy_pyworker("examples/network-edge/service-bindings-rpc/py")
    url = deploy_wrangler("examples/network-edge/service-bindings-rpc/ts")
    record_url("service-bindings", url)


def prepare_websockets() -> None:
    require_remote_prepare("websockets")
    url = deploy_pyworker("examples/state-events/durable-object-chatroom")
    record_url("websockets", url)


def account_id_from_wrangler() -> str | None:
    proc = run(["npx", "--yes", "wrangler", "whoami"], check=False)
    matches = re.findall(r"[0-9a-f]{32}", proc.stdout)
    if matches:
        return matches[0]
    return None


def prepare_browser_rendering() -> None:
    require_remote_prepare("browser-rendering")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or account_id_from_wrangler()
    if not account_id:
        raise SystemExit("Could not determine CLOUDFLARE_ACCOUNT_ID from env or wrangler whoami.")
    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        raise SystemExit(
            "Browser Rendering REST verification still needs CLOUDFLARE_API_TOKEN "
            "with Browser Rendering permission."
        )
    print(f"Browser Rendering preflight ready for account {account_id}.")
    print("Remote verifier will write ACCOUNT_ID and CF_API_TOKEN to a temporary .dev.vars file.")


def ensure_r2_bucket(name: str) -> None:
    proc = run(["npx", "--yes", "wrangler", "r2", "bucket", "list"], check=False)
    if proc.returncode == 0 and name in proc.stdout:
        print(f"R2 bucket exists: {name}")
        return
    run_print(["npx", "--yes", "wrangler", "r2", "bucket", "create", name])


def enable_catalog(name: str) -> str:
    proc = run(["npx", "--yes", "wrangler", "r2", "bucket", "catalog", "get", name], check=False)
    if proc.returncode == 0 and "not enabled" not in proc.stdout.lower():
        print(f"R2 Data Catalog already enabled for bucket: {name}")
        print(proc.stdout.rstrip())
        return proc.stdout
    run_print(["npx", "--yes", "wrangler", "r2", "bucket", "catalog", "enable", name])
    get_proc = run_print(
        ["npx", "--yes", "wrangler", "r2", "bucket", "catalog", "get", name], check=False
    )
    return get_proc.stdout


def prepare_r2_catalog_prereqs(profile: str) -> None:
    require_remote_prepare(profile)
    bucket = os.environ.get("XAMPLER_R2_SQL_BUCKET", "xampler-r2-sql")
    ensure_r2_bucket(bucket)
    catalog_output = enable_catalog(bucket)
    catalog_uri_match = re.search(r"Catalog URI:\s+'?([^'\n]+)'?", catalog_output)
    warehouse_match = re.search(r"Warehouse:\s+'?([^'\n]+)'?", catalog_output)
    state = load_state()
    state.setdefault("r2-data-catalog", {})["catalog_uri"] = (
        catalog_uri_match.group(1).strip() if catalog_uri_match else ""
    )
    state.setdefault("r2-sql", {})["warehouse"] = (
        warehouse_match.group(1).strip() if warehouse_match else ""
    )
    state.setdefault("r2-sql", {})["bucket"] = bucket
    save_state(state)
    print("Next required secret step:")
    print(
        "  export WRANGLER_R2_SQL_AUTH_TOKEN=...  "
        "# token with R2 SQL/Data Catalog/R2 permissions"
    )
    print("  export XAMPLER_R2_DATA_CATALOG_TOKEN=...  # same token if allowed by its permissions")
    print("  export XAMPLER_R2_DATA_CATALOG_URI=...    # from catalog get/enable output")


def prepare_all() -> None:
    # Exclude REST-token-only preflights from all unless their credentials are present.
    for name in (
        "vectorize",
        "queues-dlq",
        "service-bindings",
        "websockets",
        "r2-sql",
        "r2-data-catalog",
    ):
        PREPARE[name]()


PREPARE = {
    "vectorize": prepare_vectorize,
    "queues-dlq": prepare_queues_dlq,
    "service-bindings": prepare_service_bindings,
    "websockets": prepare_websockets,
    "browser-rendering": prepare_browser_rendering,
    "r2-sql": lambda: prepare_r2_catalog_prereqs("r2-sql"),
    "r2-data-catalog": lambda: prepare_r2_catalog_prereqs("r2-data-catalog"),
    "all": prepare_all,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", choices=sorted(PREPARE))
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name, description in sorted(PROFILE_DESCRIPTIONS.items()):
            print(f"{name}: {description}")
        return 0
    if args.profile is None:
        parser.error("profile required unless --list is used")

    PREPARE[args.profile]()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, file=sys.stderr)
        raise
