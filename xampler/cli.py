from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

REMOTE_ENV = "XAMPLER_RUN_REMOTE"
PREPARE_ENV = "XAMPLER_PREPARE_REMOTE"
CLEANUP_ENV = "XAMPLER_CLEANUP_REMOTE"

EXAMPLES = {
    "r2": "examples/storage-data/r2-object-storage",
    "d1": "examples/storage-data/d1-database",
    "kv": "examples/storage-data/kv-namespace",
    "queues": "examples/state-events/queues-producer-consumer",
    "vectorize": "examples/ai-agents/vectorize-search",
    "workers-ai": "examples/ai-agents/workers-ai-inference",
    "browser-rendering": "examples/network-edge/browser-rendering-screenshot",
    "r2-sql": "examples/storage-data/r2-sql",
    "r2-data-catalog": "examples/storage-data/r2-data-catalog",
    "gutenberg": "examples/streaming/gutenberg-stream-composition",
    "workflows": "examples/state-events/workflows-pipeline",
    "durable-objects": "examples/state-events/durable-object-chatroom",
    "websockets": "examples/network-edge/outbound-websocket-consumer",
    "service-bindings": "examples/network-edge/service-bindings-rpc/ts",
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xc", description="Xampler Cloudflare learning CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="show local tools and credential readiness")

    verify = sub.add_parser("verify", help="run a local example verifier")
    verify.add_argument("example", choices=sorted(EXAMPLES))

    remote = sub.add_parser("remote", help="prepare, verify, or cleanup remote examples")
    remote_sub = remote.add_subparsers(dest="remote_command", required=True)
    for name in ("prepare", "verify", "cleanup"):
        cmd = remote_sub.add_parser(name)
        cmd.add_argument("example", choices=sorted(EXAMPLES))

    dev = sub.add_parser("dev", help="local package development helpers")
    dev_sub = dev.add_subparsers(dest="dev_command", required=True)
    dev_sub.add_parser("link")
    dev_sub.add_parser("restore")

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "doctor":
        return doctor()
    if args.command == "verify":
        return run([sys.executable, "scripts/verify_examples.py", EXAMPLES[args.example]])
    if args.command == "remote":
        return remote_command(args.remote_command, args.example)
    if args.command == "dev":
        extra = ["--restore"] if args.dev_command == "restore" else []
        return run([sys.executable, "scripts/use_local_xampler.py", *extra])
    return 2


def doctor() -> int:
    print("Xampler doctor")
    print(f"repo: {Path.cwd()}")
    for tool in ("uv", "pywrangler", "wrangler", "node"):
        print(f"{tool}: {_which_version(tool)}")
    print("\nRemote gates:")
    for key in (REMOTE_ENV, PREPARE_ENV, CLEANUP_ENV):
        print(f"{key}={os.environ.get(key, '0')}")
    print("\nCredentials/secrets visible to this shell:")
    for key in (
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "WRANGLER_R2_SQL_AUTH_TOKEN",
        "XAMPLER_R2_DATA_CATALOG_TOKEN",
        "OPENAI_API_KEY",
    ):
        print(f"{key}: {'set' if os.environ.get(key) else 'missing'}")
    return 0


def remote_command(action: str, example: str) -> int:
    script = {
        "prepare": "scripts/prepare_remote_examples.py",
        "verify": "scripts/verify_remote_examples.py",
        "cleanup": "scripts/cleanup_remote_examples.py",
    }[action]
    env = os.environ.copy()
    env[REMOTE_ENV] = "1"
    if action == "prepare":
        env[PREPARE_ENV] = "1"
    if action == "cleanup":
        env[CLEANUP_ENV] = "1"
    return run([sys.executable, script, example], env=env)


def run(command: list[str], *, env: dict[str, str] | None = None) -> int:
    print("+", " ".join(command))
    return subprocess.call(command, env=env)


def _which_version(tool: str) -> str:
    try:
        found = subprocess.check_output(["/usr/bin/env", "which", tool], text=True).strip()
    except subprocess.CalledProcessError:
        return "missing"
    version = ""
    with suppress(Exception):
        output = subprocess.check_output(
            [tool, "--version"], text=True, stderr=subprocess.STDOUT
        )
        version = output.splitlines()[0]
    return f"{found} {version}".strip()


if __name__ == "__main__":
    raise SystemExit(main())
