from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
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
    "ai-gateway": "examples/ai-agents/ai-gateway-chat",
    "agents": "examples/ai-agents/agents-sdk-tools",
    "cron": "examples/state-events/cron-trigger",
    "email": "examples/network-edge/email-worker-router",
    "htmlrewriter": "examples/network-edge/htmlrewriter-opengraph",
    "hyperdrive": "examples/storage-data/hyperdrive-postgres",
}

DOCS = {
    "r2": "docs/api/reference/r2.md",
    "d1": "docs/api/reference/d1.md",
    "kv": "docs/api/reference/kv.md",
    "status": "docs/api/reference/status.md",
    "vocabulary": "docs/api/vocabulary.md",
    "queues": "docs/api/reference/queues.md",
    "vectorize": "docs/api/reference/vectorize.md",
    "ai": "docs/api/reference/ai.md",
    "browser-rendering": "docs/api/reference/browser-rendering.md",
    "r2-sql": "docs/api/reference/r2-sql.md",
    "r2-data-catalog": "docs/api/reference/r2-data-catalog.md",
    "durable-objects": "docs/api/reference/durable-objects.md",
    "workflows": "docs/api/reference/workflows.md",
    "cron": "docs/api/reference/cron.md",
    "service-bindings": "docs/api/reference/service-bindings.md",
    "websockets": "docs/api/reference/websockets.md",
    "agents": "docs/api/reference/agents.md",
    "ai-gateway": "docs/api/reference/ai-gateway.md",
    "email": "docs/api/reference/email.md",
    "htmlrewriter": "docs/api/reference/htmlrewriter.md",
    "hyperdrive": "docs/api/reference/hyperdrive.md",
}


@dataclass(frozen=True)
class RemoteAdvice:
    profile: str
    credentials: tuple[str, ...]
    prepare: bool
    cost: str
    notes: tuple[str, ...] = ()


REMOTE_ADVICE = {
    "browser-rendering": RemoteAdvice(
        "browser-rendering",
        ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
        True,
        "May incur Browser Rendering usage charges.",
        ("Run `xc remote prepare browser-rendering` before verify.",),
    ),
    "r2-sql": RemoteAdvice(
        "r2-sql",
        ("CLOUDFLARE_ACCOUNT_ID", "WRANGLER_R2_SQL_AUTH_TOKEN"),
        True,
        "May create/use an R2 bucket, catalog, and R2 SQL queries.",
    ),
    "r2-data-catalog": RemoteAdvice(
        "r2-data-catalog",
        (
            "CLOUDFLARE_ACCOUNT_ID",
            "XAMPLER_R2_DATA_CATALOG_TOKEN or WRANGLER_R2_SQL_AUTH_TOKEN",
        ),
        True,
        "May create/use R2 Data Catalog namespaces/tables.",
    ),
    "ai-gateway": RemoteAdvice(
        "ai-gateway",
        (
            "CLOUDFLARE_ACCOUNT_ID",
            "CLOUDFLARE_API_TOKEN",
            "XAMPLER_AI_GATEWAY_ID",
            "OPENAI_API_KEY",
        ),
        False,
        "May incur provider costs; default model is openai/gpt-4o-mini unless "
        "XAMPLER_AI_GATEWAY_MODEL is set.",
    ),
    "vectorize": RemoteAdvice(
        "vectorize",
        ("CLOUDFLARE_ACCOUNT_ID",),
        True,
        "May create/use a Vectorize index.",
    ),
    "workers-ai": RemoteAdvice(
        "workers-ai",
        ("CLOUDFLARE_ACCOUNT_ID",),
        True,
        "May incur Workers AI usage charges.",
    ),
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xc", description="Xampler Cloudflare learning CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor", help="show local tools and credential readiness")
    doctor_parser.add_argument(
        "profile", nargs="?", choices=sorted(set(EXAMPLES) | set(REMOTE_ADVICE))
    )

    sub.add_parser("list", help="list known examples and docs")

    docs_parser = sub.add_parser("docs", help="print the docs path for a surface")
    docs_parser.add_argument("surface", choices=sorted(DOCS))

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
        return doctor(args.profile)
    if args.command == "list":
        return list_surfaces()
    if args.command == "docs":
        return show_docs(args.surface)
    if args.command == "verify":
        return run([sys.executable, "scripts/verify_examples.py", EXAMPLES[args.example]])
    if args.command == "remote":
        return remote_command(args.remote_command, args.example)
    if args.command == "dev":
        extra = ["--restore"] if args.dev_command == "restore" else []
        return run([sys.executable, "scripts/use_local_xampler.py", *extra])
    return 2


def list_surfaces() -> int:
    print("Examples:")
    for name, path in sorted(EXAMPLES.items()):
        print(f"  {name:18} {path}")
    print("\nDocs:")
    for name, path in sorted(DOCS.items()):
        print(f"  {name:18} {path}")
    return 0


def show_docs(surface: str) -> int:
    print(DOCS[surface])
    return 0


def doctor(profile: str | None = None) -> int:
    print("Xampler doctor")
    print(f"repo: {Path.cwd()}")
    for tool in ("uv", "pywrangler", "wrangler", "node"):
        print(f"{tool}: {_which_version(tool)}")
    print("\nRemote gates:")
    for key in (REMOTE_ENV, PREPARE_ENV, CLEANUP_ENV):
        print(f"{key}={os.environ.get(key, '0')}")
    if profile is None:
        print("\nCredentials/secrets visible to this shell:")
        keys = sorted({key for advice in REMOTE_ADVICE.values() for key in advice.credentials})
        for key in keys:
            print(f"{key}: {_credential_status(key)}")
        print("\nTip: run `xc doctor <profile>` for profile-specific advice.")
        return 0
    print(f"\nProfile: {profile}")
    if profile in EXAMPLES:
        print(f"example: {EXAMPLES[profile]}")
    advice = REMOTE_ADVICE.get(profile)
    if advice is None:
        print("No remote credential advice for this profile yet.")
        return 0
    print(f"cost warning: {advice.cost}")
    print("required credentials:")
    for key in advice.credentials:
        print(f"  {key}: {_credential_status(key)}")
    print("recommended remote flow:")
    if advice.prepare:
        print(f"  xc remote prepare {profile}")
    print(f"  xc remote verify {profile}")
    if advice.prepare:
        print(f"  xc remote cleanup {profile}")
    for note in advice.notes:
        print(f"note: {note}")
    return 0


def _credential_status(name: str) -> str:
    if " or " in name:
        any_set = any(os.environ.get(part.strip()) for part in name.split(" or "))
        return "set" if any_set else "missing"
    return "set" if os.environ.get(name) else "missing"


def remote_command(action: str, example: str) -> int:
    advice = REMOTE_ADVICE.get(example)
    if advice is not None:
        print(f"Remote cost warning: {advice.cost}")
        print(f"Run `xc doctor {example}` to inspect required credentials.")
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
