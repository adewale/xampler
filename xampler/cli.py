from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, NoReturn, cast

EXIT_OK = 0
EXIT_VERIFIER_FAILURE = 1
EXIT_USAGE = 2
EXIT_MISSING_CREDENTIALS = 3
EXIT_PROVIDER_FAILURE = 4
EXIT_REMOTE_SKIPPED = 5

REMOTE_ENV = "XAMPLER_RUN_REMOTE"
PREPARE_ENV = "XAMPLER_PREPARE_REMOTE"
CLEANUP_ENV = "XAMPLER_CLEANUP_REMOTE"


class XamplerArgumentParser(argparse.ArgumentParser):
    json_errors_enabled: ClassVar[bool] = False

    def error(self, message: str) -> NoReturn:
        if self.json_errors_enabled:
            print(
                json.dumps(
                    {"error": {"code": "bad_request", "message": message, "status": EXIT_USAGE}}
                ),
                file=sys.stderr,
            )
            raise SystemExit(EXIT_USAGE)
        super().error(message)


@dataclass(frozen=True)
class RemoteAdvice:
    credentials: tuple[str, ...]
    prepare: bool
    cost: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Surface:
    name: str
    example: str | None = None
    docs: str | None = None
    remote: RemoteAdvice | None = None


def _empty_env() -> Mapping[str, str]:
    return {}


@dataclass(frozen=True)
class CommandPlan:
    action: str
    surface: str
    command: tuple[str, ...]
    env: Mapping[str, str] = field(default_factory=_empty_env)
    cwd: str | None = None
    mutates: bool = False
    cost_warning: str | None = None
    description: str | None = None

    def payload(self, *, dry_run: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "action": self.action,
            "surface": self.surface,
            "command": list(self.command),
            "env": dict(self.env),
            "mutates": self.mutates,
            "dry_run": dry_run,
        }
        if self.cwd is not None:
            payload["cwd"] = self.cwd
        if self.cost_warning is not None:
            payload["cost_warning"] = self.cost_warning
        if self.description is not None:
            payload["description"] = self.description
        return payload


@dataclass(frozen=True)
class CliOptions:
    json_output: bool = False
    dry_run: bool = False
    quiet: bool = False
    verbose: int = 0


SURFACES: dict[str, Surface] = {
    "agents": Surface(
        "agents", "examples/ai-agents/agents-sdk-tools", "docs/api/reference/agents.md"
    ),
    "ai": Surface("ai", "examples/ai-agents/workers-ai-inference", "docs/api/reference/ai.md"),
    "ai-gateway": Surface(
        "ai-gateway",
        "examples/ai-agents/ai-gateway-chat",
        "docs/api/reference/ai-gateway.md",
        RemoteAdvice(
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
    ),
    "browser-rendering": Surface(
        "browser-rendering",
        "examples/network-edge/browser-rendering-screenshot",
        "docs/api/reference/browser-rendering.md",
        RemoteAdvice(
            ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
            True,
            "May incur Browser Rendering usage charges.",
            ("Run `xc remote prepare browser-rendering` before verify.",),
        ),
    ),
    "cron": Surface("cron", "examples/state-events/cron-trigger", "docs/api/reference/cron.md"),
    "d1": Surface("d1", "examples/storage-data/d1-database", "docs/api/reference/d1.md"),
    "durable-objects": Surface(
        "durable-objects",
        "examples/state-events/durable-object-chatroom",
        "docs/api/reference/durable-objects.md",
    ),
    "dynamic-workers": Surface(
        "dynamic-workers",
        "examples/experimental/dynamic-workers-loader",
        "docs/api/reference/dynamic-workers.md",
    ),
    "email": Surface(
        "email", "examples/network-edge/email-worker-router", "docs/api/reference/email.md"
    ),
    "gutenberg": Surface("gutenberg", "examples/streaming/gutenberg-stream-composition"),
    "htmlrewriter": Surface(
        "htmlrewriter",
        "examples/network-edge/htmlrewriter-opengraph",
        "docs/api/reference/htmlrewriter.md",
    ),
    "hyperdrive": Surface(
        "hyperdrive",
        "examples/storage-data/hyperdrive-postgres",
        "docs/api/reference/hyperdrive.md",
    ),
    "kv": Surface("kv", "examples/storage-data/kv-namespace", "docs/api/reference/kv.md"),
    "mini-wiki": Surface("mini-wiki", "examples/full-apps/mini-wiki"),
    "python-by-example": Surface(
        "python-by-example", "examples/experimental/python-by-example-playground"
    ),
    "queues": Surface(
        "queues", "examples/state-events/queues-producer-consumer", "docs/api/reference/queues.md"
    ),
    "r2": Surface("r2", "examples/storage-data/r2-object-storage", "docs/api/reference/r2.md"),
    "r2-data-catalog": Surface(
        "r2-data-catalog",
        "examples/storage-data/r2-data-catalog",
        "docs/api/reference/r2-data-catalog.md",
        RemoteAdvice(
            (
                "CLOUDFLARE_ACCOUNT_ID",
                "XAMPLER_R2_DATA_CATALOG_TOKEN or WRANGLER_R2_SQL_AUTH_TOKEN",
            ),
            True,
            "May create/use R2 Data Catalog namespaces/tables.",
        ),
    ),
    "r2-sql": Surface(
        "r2-sql",
        "examples/storage-data/r2-sql",
        "docs/api/reference/r2-sql.md",
        RemoteAdvice(
            ("CLOUDFLARE_ACCOUNT_ID", "WRANGLER_R2_SQL_AUTH_TOKEN"),
            True,
            "May create/use an R2 bucket, catalog, and R2 SQL queries.",
        ),
    ),
    "service-bindings": Surface(
        "service-bindings",
        "examples/network-edge/service-bindings-rpc/ts",
        "docs/api/reference/service-bindings.md",
    ),
    "status": Surface("status", docs="docs/api/reference/status.md"),
    "vectorize": Surface(
        "vectorize",
        "examples/ai-agents/vectorize-search",
        "docs/api/reference/vectorize.md",
        RemoteAdvice(("CLOUDFLARE_ACCOUNT_ID",), True, "May create/use a Vectorize index."),
    ),
    "vocabulary": Surface("vocabulary", docs="docs/api/vocabulary.md"),
    "websockets": Surface(
        "websockets",
        "examples/network-edge/outbound-websocket-consumer",
        "docs/api/reference/websockets.md",
    ),
    "workers-ai": Surface(
        "workers-ai",
        "examples/ai-agents/workers-ai-inference",
        None,
        RemoteAdvice(("CLOUDFLARE_ACCOUNT_ID",), True, "May incur Workers AI usage charges."),
    ),
    "workflows": Surface(
        "workflows", "examples/state-events/workflows-pipeline", "docs/api/reference/workflows.md"
    ),
}


def _examples() -> dict[str, str]:
    return {
        name: surface.example
        for name, surface in SURFACES.items()
        if surface.example is not None
    }


def _docs() -> dict[str, str]:
    return {name: surface.docs for name, surface in SURFACES.items() if surface.docs is not None}


def _surface_choices(*, require_example: bool = False, require_docs: bool = False) -> list[str]:
    return sorted(
        name
        for name, surface in SURFACES.items()
        if (not require_example or surface.example is not None)
        and (not require_docs or surface.docs is not None)
    )


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    json_requested = "--json" in raw_args
    XamplerArgumentParser.json_errors_enabled = json_requested

    parser = XamplerArgumentParser(prog="xc", description="Xampler Cloudflare learning CLI")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--dry-run", action="store_true", help="plan commands without executing")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress progress output")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=XamplerArgumentParser)

    doctor_parser = sub.add_parser("doctor", help="show local tools and credential readiness")
    doctor_parser.add_argument("surface", nargs="?", choices=_surface_choices())

    docs_parser = sub.add_parser("docs", help="documentation helpers")
    docs_sub = docs_parser.add_subparsers(dest="docs_command", required=True)
    docs_sub.add_parser("list", help="list docs surfaces")
    docs_path = docs_sub.add_parser("path", help="print the docs path for a surface")
    docs_path.add_argument("surface", choices=_surface_choices(require_docs=True))

    examples = sub.add_parser("examples", help="example helpers")
    examples_sub = examples.add_subparsers(dest="examples_command", required=True)
    examples_sub.add_parser("list", help="list known examples")
    examples_verify = examples_sub.add_parser("verify", help="run a local example verifier")
    examples_verify.add_argument("surface", choices=_surface_choices(require_example=True))

    remote = sub.add_parser("remote", help="plan, prepare, verify, or cleanup remote examples")
    remote_sub = remote.add_subparsers(dest="remote_command", required=True)
    for name in ("plan", "prepare", "verify", "cleanup"):
        cmd = remote_sub.add_parser(name)
        cmd.add_argument("surface", choices=_surface_choices(require_example=True))
        cmd.add_argument(
            "--dry-run",
            dest="command_dry_run",
            action="store_true",
            help="print the planned remote command",
        )

    dev = sub.add_parser("dev", help="local package development helpers")
    dev_sub = dev.add_subparsers(dest="dev_command", required=True)
    dev_sub.add_parser("link")
    dev_sub.add_parser("restore")

    args = parser.parse_args(raw_args)
    options = CliOptions(
        json_output=bool(args.json),
        dry_run=bool(args.dry_run) or bool(getattr(args, "command_dry_run", False)),
        quiet=bool(args.quiet),
        verbose=int(args.verbose),
    )

    if args.command == "doctor":
        return doctor(args.surface, options=options)
    if args.command == "docs":
        if args.docs_command == "list":
            return list_docs(options=options)
        return show_docs(args.surface, options=options)
    if args.command == "examples":
        if args.examples_command == "list":
            return list_examples(options=options)
        return execute_plan(local_verify_plan(args.surface), options=options)
    if args.command == "remote":
        return remote_command(args.remote_command, args.surface, options=options)
    if args.command == "dev":
        return execute_plan(dev_plan(args.dev_command), options=options)
    return EXIT_USAGE


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _progress(message: str, *, options: CliOptions) -> None:
    if not options.quiet:
        print(message, file=sys.stderr)


def list_surfaces(*, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    if opts.json_output:
        _emit_json({
            "examples": dict(sorted(_examples().items())),
            "docs": dict(sorted(_docs().items())),
        })
        return EXIT_OK
    print("Examples:")
    for name, path in sorted(_examples().items()):
        print(f"  {name:18} {path}")
    print("\nDocs:")
    for name, path in sorted(_docs().items()):
        print(f"  {name:18} {path}")
    return EXIT_OK


def list_examples(*, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    examples = dict(sorted(_examples().items()))
    if opts.json_output:
        _emit_json({"examples": examples})
        return EXIT_OK
    for name, path in examples.items():
        print(f"{name:18} {path}")
    return EXIT_OK


def list_docs(*, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    docs = dict(sorted(_docs().items()))
    if opts.json_output:
        _emit_json({"docs": docs})
        return EXIT_OK
    for name, path in docs.items():
        print(f"{name:18} {path}")
    return EXIT_OK


def show_docs(surface: str, *, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    path = _docs()[surface]
    if opts.json_output:
        _emit_json({"surface": surface, "path": path})
        return EXIT_OK
    print(path)
    return EXIT_OK


def _doctor_payload(surface_name: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "repo": str(Path.cwd()),
        "tools": {tool: _which_version(tool) for tool in ("uv", "pywrangler", "wrangler", "node")},
        "remote_gates": {
            key: os.environ.get(key, "0") for key in (REMOTE_ENV, PREPARE_ENV, CLEANUP_ENV)
        },
        "exit_codes": {
            "ok": EXIT_OK,
            "verifier_failure": EXIT_VERIFIER_FAILURE,
            "usage": EXIT_USAGE,
            "missing_credentials": EXIT_MISSING_CREDENTIALS,
            "provider_failure": EXIT_PROVIDER_FAILURE,
            "remote_skipped": EXIT_REMOTE_SKIPPED,
        },
    }
    if surface_name is None:
        keys = sorted(
            {
                key
                for surface in SURFACES.values()
                if surface.remote
                for key in surface.remote.credentials
            }
        )
        payload["credentials"] = {key: _credential_status(key) for key in keys}
        payload["tip"] = "run `xc doctor <surface>` for surface-specific advice"
        return payload

    surface = SURFACES[surface_name]
    payload["surface"] = surface_name
    payload["profile"] = surface_name
    if surface.example is not None:
        payload["example"] = surface.example
    if surface.docs is not None:
        payload["docs"] = surface.docs
    advice = surface.remote
    if advice is None:
        payload["remote_advice"] = None
        payload["notes"] = ["No remote credential advice for this surface yet."]
        return payload
    remote_flow: list[str] = []
    if advice.prepare:
        remote_flow.append(f"xc remote prepare {surface_name}")
    remote_flow.append(f"xc remote verify {surface_name}")
    if advice.prepare:
        remote_flow.append(f"xc remote cleanup {surface_name}")
    payload.update(
        {
            "cost_warning": advice.cost,
            "credentials": {key: _credential_status(key) for key in advice.credentials},
            "remote_flow": remote_flow,
            "notes": list(advice.notes),
        }
    )
    return payload


def doctor(surface: str | None = None, *, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    payload = _doctor_payload(surface)
    if opts.json_output:
        _emit_json(payload)
        return EXIT_OK

    print("Xampler doctor")
    print(f"repo: {payload['repo']}")
    for tool, status in cast(dict[str, str], payload["tools"]).items():
        print(f"{tool}: {status}")
    print("\nRemote gates:")
    for key, value in cast(dict[str, str], payload["remote_gates"]).items():
        print(f"{key}={value}")
    if surface is None:
        print("\nCredentials/secrets visible to this shell:")
        for key, status in cast(dict[str, str], payload["credentials"]).items():
            print(f"{key}: {status}")
        print("\nTip: run `xc doctor <surface>` for surface-specific advice.")
        return EXIT_OK

    print(f"\nSurface: {surface}")
    if "example" in payload:
        print(f"example: {payload['example']}")
    if "docs" in payload:
        print(f"docs: {payload['docs']}")
    if payload.get("remote_advice") is None and "cost_warning" not in payload:
        print("No remote credential advice for this surface yet.")
        return EXIT_OK
    print(f"cost warning: {payload['cost_warning']}")
    print("required credentials:")
    for key, status in cast(dict[str, str], payload["credentials"]).items():
        print(f"  {key}: {status}")
    print("recommended remote flow:")
    for command in cast(list[str], payload["remote_flow"]):
        print(f"  {command}")
    for note in cast(list[str], payload["notes"]):
        print(f"note: {note}")
    return EXIT_OK


def _credential_status(name: str) -> str:
    if " or " in name:
        any_set = any(os.environ.get(part.strip()) for part in name.split(" or "))
        return "set" if any_set else "missing"
    return "set" if os.environ.get(name) else "missing"


def local_verify_plan(surface: str) -> CommandPlan:
    example = _examples()[surface]
    return CommandPlan(
        action="verify",
        surface=surface,
        command=(sys.executable, "scripts/verify_examples.py", example),
        description=f"Verify {surface} locally with pywrangler",
    )


def dev_plan(action: str) -> CommandPlan:
    extra = ("--restore",) if action == "restore" else ()
    return CommandPlan(
        action=f"dev:{action}",
        surface="xampler",
        command=(sys.executable, "scripts/use_local_xampler.py", *extra),
        mutates=True,
        description=f"Run local package development helper: {action}",
    )


def remote_plan(action: str, surface_name: str) -> CommandPlan:
    surface = SURFACES[surface_name]
    planned_action = action
    if action == "plan":
        planned_action = (
            "prepare" if surface.remote is not None and surface.remote.prepare else "verify"
        )
    script = {
        "prepare": "scripts/prepare_remote_examples.py",
        "verify": "scripts/verify_remote_examples.py",
        "cleanup": "scripts/cleanup_remote_examples.py",
    }[planned_action]
    env: dict[str, str] = {REMOTE_ENV: "1"}
    if planned_action == "prepare":
        env[PREPARE_ENV] = "1"
    if planned_action == "cleanup":
        env[CLEANUP_ENV] = "1"
    return CommandPlan(
        action=planned_action,
        surface=surface_name,
        command=(sys.executable, script, surface_name),
        env=env,
        mutates=planned_action in {"prepare", "cleanup"},
        cost_warning=surface.remote.cost if surface.remote is not None else None,
        description=f"Remote {planned_action} for {surface_name}",
    )


def execute_plan(plan: CommandPlan, *, options: CliOptions) -> int:
    if options.dry_run:
        payload = plan.payload(dry_run=True)
        if options.json_output:
            _emit_json(payload)
        else:
            print(f"dry-run: {' '.join(plan.command)}")
            for key, value in plan.env.items():
                print(f"env {key}={value}")
        return EXIT_OK
    if plan.cost_warning is not None:
        _progress(f"Remote cost warning: {plan.cost_warning}", options=options)
        _progress(
            f"Run `xc doctor {plan.surface}` to inspect required credentials.",
            options=options,
        )
    env = os.environ.copy()
    env.update(plan.env)
    return run(list(plan.command), env=env, cwd=plan.cwd, quiet=options.quiet)


def remote_command(action: str, surface: str, *, options: CliOptions) -> int:
    plan = remote_plan(action, surface)
    if action == "plan":
        if options.json_output:
            _emit_json(plan.payload(dry_run=True))
        else:
            print(f"remote plan for {surface}: {' '.join(plan.command)}")
            for key, value in plan.env.items():
                print(f"env {key}={value}")
        return EXIT_OK
    return execute_plan(plan, options=options)


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
    quiet: bool = False,
) -> int:
    if not quiet:
        print("+", " ".join(command), file=sys.stderr)
    return subprocess.call(command, env=env, cwd=cwd)


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


__all__ = [
    "EXIT_MISSING_CREDENTIALS",
    "EXIT_OK",
    "EXIT_PROVIDER_FAILURE",
    "EXIT_REMOTE_SKIPPED",
    "EXIT_USAGE",
    "EXIT_VERIFIER_FAILURE",
    "CliOptions",
    "CommandPlan",
    "RemoteAdvice",
    "SURFACES",
    "Surface",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
