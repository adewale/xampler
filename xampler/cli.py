from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import ClassVar, NoReturn

from xampler.cli_models import (
    EXIT_MISSING_CREDENTIALS,
    EXIT_OK,
    EXIT_PROVIDER_FAILURE,
    EXIT_REMOTE_SKIPPED,
    EXIT_USAGE,
    EXIT_VERIFIER_FAILURE,
    CliOptions,
    CommandPlan,
    RemoteAdvice,
    Surface,
)
from xampler.cli_registry import SURFACES, surface_choices
from xampler.cli_runtime import (
    dev_plan,
    doctor,
    execute_plan,
    list_docs,
    list_examples,
    local_verify_plan,
    remote_command,
    run,
    show_docs,
    which_version,
)


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
    doctor_parser.add_argument("surface", nargs="?", choices=surface_choices())

    docs_parser = sub.add_parser("docs", help="documentation helpers")
    docs_sub = docs_parser.add_subparsers(dest="docs_command", required=True)
    docs_sub.add_parser("list", help="list docs surfaces")
    docs_path = docs_sub.add_parser("path", help="print the docs path for a surface")
    docs_path.add_argument("surface", choices=surface_choices(require_docs=True))

    examples = sub.add_parser("examples", help="example helpers")
    examples_sub = examples.add_subparsers(dest="examples_command", required=True)
    examples_sub.add_parser("list", help="list known examples")
    examples_verify = examples_sub.add_parser("verify", help="run a local example verifier")
    examples_verify.add_argument("surface", choices=surface_choices(require_example=True))

    remote = sub.add_parser("remote", help="plan, prepare, verify, or cleanup remote examples")
    remote_sub = remote.add_subparsers(dest="remote_command", required=True)
    for name in ("plan", "prepare", "verify", "cleanup"):
        cmd = remote_sub.add_parser(name)
        cmd.add_argument("surface", choices=surface_choices(require_example=True))
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
    "run",
    "which_version",
]


if __name__ == "__main__":
    raise SystemExit(main())
