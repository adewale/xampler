#!/usr/bin/env python3
"""Clean up remote resources created by scripts/prepare_remote_examples.py.

Cleanup is intentionally gated because it deletes deployed Workers and, with
--include-data, product resources such as queues, Vectorize indexes, and R2
buckets.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".xampler-remote-state.json"

WORKERS_BY_PROFILE = {
    "workers-ai": ["xampler-ai-agents-workers-ai-inference"],
    "vectorize": ["xampler-ai-agents-vectorize-search"],
    "queues-dlq": ["xampler-state-events-queues-producer-consumer"],
    "service-bindings": [
        "xampler-network-edge-service-bindings-rpc-ts",
        "xampler-network-edge-service-bindings-rpc-py",
    ],
    "websockets": ["xampler-state-events-durable-object-chatroom"],
    "browser-rendering": ["xampler-network-edge-browser-rendering-screenshot"],
    "r2-sql": ["xampler-storage-data-r2-sql"],
    "r2-data-catalog": ["xampler-storage-data-r2-data-catalog"],
}

DATA_RESOURCES_BY_PROFILE = {
    "vectorize": [
        ["npx", "--yes", "wrangler", "vectorize", "delete", "xampler-vectorize", "--force"]
    ],
    "queues-dlq": [
        ["npx", "--yes", "wrangler", "queues", "delete", "xampler-jobs"],
        ["npx", "--yes", "wrangler", "queues", "delete", "xampler-jobs-dlq"],
    ],
    "r2-sql": [["npx", "--yes", "wrangler", "r2", "bucket", "delete", "xampler-r2-sql"]],
    "r2-data-catalog": [["npx", "--yes", "wrangler", "r2", "bucket", "delete", "xampler-r2-sql"]],
}


def token_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def require_cleanup() -> None:
    if (
        os.environ.get("XAMPLER_RUN_REMOTE") != "1"
        or os.environ.get("XAMPLER_CLEANUP_REMOTE") != "1"
    ):
        raise SystemExit(
            "Refusing cleanup: set XAMPLER_RUN_REMOTE=1 and XAMPLER_CLEANUP_REMOTE=1."
        )


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    proc = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.returncode != 0:
        print(f"warning: command exited {proc.returncode}")


def load_state() -> dict[str, dict[str, str]]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, dict[str, str]]) -> None:
    if state:
        STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    else:
        STATE_PATH.unlink(missing_ok=True)


def catalog_request(catalog_uri: str, token: str, method: str, path: str) -> tuple[int, str]:
    request = urllib.request.Request(
        f"{catalog_uri.rstrip('/')}{path}",
        method=method,
        headers={
            "authorization": f"Bearer {token}",
            "user-agent": "xampler-remote-cleanup/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")


def cleanup_catalog_seed_resources() -> None:
    state = load_state()
    catalog_uri = state.get("r2-data-catalog", {}).get("catalog_uri")
    token = token_env("XAMPLER_R2_DATA_CATALOG_TOKEN", "WRANGLER_R2_SQL_AUTH_TOKEN")
    if not catalog_uri or not token:
        print("warning: skip catalog table cleanup; missing catalog URI or catalog token")
        return
    for method, path in [
        ("DELETE", "/v1/namespaces/xampler/tables/gutenberg_smoke"),
        ("DELETE", "/v1/namespaces/xampler_verify/tables/temp_table"),
        ("DELETE", "/v1/namespaces/xampler_verify"),
    ]:
        status, body = catalog_request(catalog_uri, token, method, path)
        if status not in {200, 204, 404}:
            print(f"warning: catalog cleanup {method} {path} -> {status}: {body}")
        else:
            print(f"catalog cleanup {method} {path} -> {status}")


def cleanup_profile(profile: str, *, include_data: bool) -> None:
    for worker in WORKERS_BY_PROFILE.get(profile, []):
        run(["npx", "--yes", "wrangler", "delete", worker, "--force"])
    if include_data:
        if profile in {"r2-sql", "r2-data-catalog"}:
            cleanup_catalog_seed_resources()
        for command in DATA_RESOURCES_BY_PROFILE.get(profile, []):
            run(command)
    state = load_state()
    state.pop(profile, None)
    save_state(state)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=[*sorted(WORKERS_BY_PROFILE), "all"])
    parser.add_argument(
        "--include-data",
        action="store_true",
        help="Also delete product resources such as queues, Vectorize indexes, and R2 buckets.",
    )
    args = parser.parse_args()
    require_cleanup()
    profiles = sorted(WORKERS_BY_PROFILE) if args.profile == "all" else [args.profile]
    for profile in profiles:
        cleanup_profile(profile, include_data=args.include_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
