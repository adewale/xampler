from __future__ import annotations

import contextlib
import io
import json
from collections.abc import Sequence

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

import xampler.cli as cli
import xampler.cli_runtime as cli_runtime


def run_cli(argv: Sequence[str]) -> tuple[str, int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    kind = "return"
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(list(argv))
    except SystemExit as exc:
        kind = "system_exit"
        code = exc.code if isinstance(exc.code, int) else 1
    return kind, code, stdout.getvalue(), stderr.getvalue()


@pytest.fixture(autouse=True)
def no_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(
        command: list[str],
        *,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        quiet: bool = False,
    ) -> int:
        return 0

    monkeypatch.setattr(cli_runtime, "run", fake_run)
    monkeypatch.setattr(
        cli_runtime, "which_version", lambda tool: f"/fake/{tool} {tool} 0.0"
    )


def assert_cli_invariants(argv: list[str], *, expect_success: bool | None = None) -> None:
    kind, code, out, err = run_cli(argv)
    assert isinstance(code, int), argv
    assert code in {
        cli.EXIT_OK,
        cli.EXIT_VERIFIER_FAILURE,
        cli.EXIT_USAGE,
        cli.EXIT_MISSING_CREDENTIALS,
        cli.EXIT_PROVIDER_FAILURE,
        cli.EXIT_REMOTE_SKIPPED,
    }, argv
    assert "Traceback" not in out
    assert "Traceback" not in err
    if expect_success is True:
        assert code == cli.EXIT_OK, (argv, out, err)
    if expect_success is False:
        assert code != cli.EXIT_OK, argv
    if "--json" in argv:
        if kind == "system_exit" and code == cli.EXIT_USAGE:
            payload = json.loads(err)
            assert payload["error"]["code"] == "bad_request"
            assert payload["error"]["status"] == cli.EXIT_USAGE
        if code == cli.EXIT_OK and out.strip():
            json.loads(out)


def test_cli_exhaustive_valid_surface_matrix() -> None:
    cases: list[list[str]] = []
    prefixes = [[], ["--json"], ["--dry-run"], ["--json", "--dry-run"], ["--quiet"], ["-v"]]
    for prefix in prefixes:
        cases.append([*prefix, "doctor"])
        for surface in cli.SURFACES:
            cases.append([*prefix, "doctor", surface])
        cases.append([*prefix, "examples", "list"])
        cases.append([*prefix, "docs", "list"])
        for surface, model in cli.SURFACES.items():
            if model.example is not None:
                cases.append([*prefix, "examples", "verify", surface])
                for action in ("plan", "prepare", "verify", "cleanup"):
                    cases.append([*prefix, "remote", action, surface])
            if model.docs is not None:
                cases.append([*prefix, "docs", "path", surface])
        for action in ("link", "restore"):
            cases.append([*prefix, "dev", action])

    for argv in cases:
        assert_cli_invariants(argv, expect_success=True)


FUZZ_ATOMS = [
    "doctor",
    "docs",
    "list",
    "path",
    "examples",
    "verify",
    "remote",
    "plan",
    "prepare",
    "cleanup",
    "dev",
    "link",
    "restore",
    "--json",
    "--dry-run",
    "--quiet",
    "-q",
    "-v",
    "--verbose",
    *cli.SURFACES,
    "",
    "--wat",
    "---",
    "missing",
    "../../x",
    "💥",
    "LIST",
    "Verify",
]


# Hypothesis shrinks a failing argv to a minimal one, which the old fixed-seed random loop
# could not do. The budget comes from the "xampler" profile in tests/conftest.py: 100
# derandomized examples plus the explicit ones below, the same on every run.
@given(argv=st.lists(st.sampled_from(FUZZ_ATOMS), max_size=8))
@example(argv=[])
@example(argv=["--json", "--wat"])
@example(argv=["--json", "examples", "verify", "missing"])
def test_cli_random_argument_fuzz(argv: list[str]) -> None:
    assert_cli_invariants(argv)


@pytest.mark.parametrize("argv", [["list"], ["verify", "r2"], ["docs", "r2"]])
def test_removed_compatibility_aliases_fail_cleanly(argv: list[str]) -> None:
    assert_cli_invariants(argv, expect_success=False)
