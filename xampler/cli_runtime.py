from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

from xampler.cli_models import (
    CLEANUP_ENV,
    EXIT_MISSING_CREDENTIALS,
    EXIT_OK,
    EXIT_PROVIDER_FAILURE,
    EXIT_REMOTE_SKIPPED,
    EXIT_USAGE,
    EXIT_VERIFIER_FAILURE,
    PREPARE_ENV,
    REMOTE_ENV,
    CliOptions,
    CommandPlan,
)
from xampler.cli_registry import SURFACES, credential_status, docs, examples


def emit_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def progress(message: str, *, options: CliOptions) -> None:
    if not options.quiet:
        print(message, file=sys.stderr)


def list_surfaces(*, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    if opts.json_output:
        emit_json({
            "examples": dict(sorted(examples().items())),
            "docs": dict(sorted(docs().items())),
        })
        return EXIT_OK
    print("Examples:")
    for name, path in sorted(examples().items()):
        print(f"  {name:18} {path}")
    print("\nDocs:")
    for name, path in sorted(docs().items()):
        print(f"  {name:18} {path}")
    return EXIT_OK


def list_examples(*, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    payload = dict(sorted(examples().items()))
    if opts.json_output:
        emit_json({"examples": payload})
        return EXIT_OK
    for name, path in payload.items():
        print(f"{name:18} {path}")
    return EXIT_OK


def list_docs(*, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    payload = dict(sorted(docs().items()))
    if opts.json_output:
        emit_json({"docs": payload})
        return EXIT_OK
    for name, path in payload.items():
        print(f"{name:18} {path}")
    return EXIT_OK


def show_docs(surface: str, *, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    path = docs()[surface]
    if opts.json_output:
        emit_json({"surface": surface, "path": path})
        return EXIT_OK
    print(path)
    return EXIT_OK


def doctor_payload(surface_name: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "repo": str(Path.cwd()),
        "tools": {tool: which_version(tool) for tool in ("uv", "pywrangler", "wrangler", "node")},
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
        payload["credentials"] = {key: credential_status(key) for key in keys}
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
            "credentials": {key: credential_status(key) for key in advice.credentials},
            "remote_flow": remote_flow,
            "notes": list(advice.notes),
        }
    )
    return payload


def doctor(surface: str | None = None, *, options: CliOptions | None = None) -> int:
    opts = options or CliOptions()
    payload = doctor_payload(surface)
    if opts.json_output:
        emit_json(payload)
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


def local_verify_plan(surface: str) -> CommandPlan:
    example = examples()[surface]
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
            emit_json(payload)
        else:
            print(f"dry-run: {' '.join(plan.command)}")
            for key, value in plan.env.items():
                print(f"env {key}={value}")
        return EXIT_OK
    if plan.cost_warning is not None:
        progress(f"Remote cost warning: {plan.cost_warning}", options=options)
        progress(
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
            emit_json(plan.payload(dry_run=True))
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


def which_version(tool: str) -> str:
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
