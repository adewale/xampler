from __future__ import annotations

import json
import os

import pytest

from xampler.cli import EXIT_OK, EXIT_USAGE, main


def test_cli_list_and_docs(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["examples", "list"]) == EXIT_OK
    assert "r2" in capsys.readouterr().out

    assert main(["docs", "path", "r2"]) == EXIT_OK
    assert "docs/api/reference/r2.md" in capsys.readouterr().out


def test_cli_doctor_profile(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setitem(os.environ, "WRANGLER_R2_SQL_AUTH_TOKEN", "token")
    assert main(["doctor", "r2-sql"]) == EXIT_OK
    output = capsys.readouterr().out
    assert "xc remote prepare r2-sql" in output
    assert "WRANGLER_R2_SQL_AUTH_TOKEN: set" in output
    assert "cost warning" in output


def test_cli_json_list_and_doctor(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setitem(os.environ, "WRANGLER_R2_SQL_AUTH_TOKEN", "token")

    assert main(["--json", "examples", "list"]) == EXIT_OK
    listed = json.loads(capsys.readouterr().out)
    assert listed["examples"]["r2"].endswith("r2-object-storage")

    assert main(["--json", "docs", "list"]) == EXIT_OK
    docs = json.loads(capsys.readouterr().out)
    assert docs["docs"]["r2"] == "docs/api/reference/r2.md"

    assert main(["--json", "doctor", "r2-sql"]) == EXIT_OK
    doctor = json.loads(capsys.readouterr().out)
    assert doctor["profile"] == "r2-sql"
    assert doctor["credentials"]["WRANGLER_R2_SQL_AUTH_TOKEN"] == "set"
    assert doctor["remote_flow"] == [
        "xc remote prepare r2-sql",
        "xc remote verify r2-sql",
        "xc remote cleanup r2-sql",
    ]


def test_cli_json_parse_errors_use_stable_envelope(capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as exc_info:
        main(["--json", "docs", "missing-surface"])

    assert exc_info.value.code == EXIT_USAGE
    payload = json.loads(capsys.readouterr().err)
    assert payload["error"]["code"] == "bad_request"
    assert payload["error"]["status"] == 2


def test_cli_remote_plan_and_dry_run_are_json_and_do_not_run(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    calls: list[object] = []

    def fake_run(*args: object, **kwargs: object) -> int:
        calls.append((args, kwargs))
        return 0

    monkeypatch.setattr("xampler.cli_runtime.run", fake_run)
    assert main(["--json", "remote", "plan", "r2-sql"]) == EXIT_OK
    plan = json.loads(capsys.readouterr().out)
    assert plan["action"] == "prepare"
    assert plan["surface"] == "r2-sql"
    assert plan["mutates"] is True
    assert plan["env"]["XAMPLER_RUN_REMOTE"] == "1"
    assert plan["env"]["XAMPLER_PREPARE_REMOTE"] == "1"

    assert main(["--json", "remote", "prepare", "r2-sql", "--dry-run"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["action"] == "prepare"
    assert payload["surface"] == "r2-sql"
    assert payload["env"]["XAMPLER_RUN_REMOTE"] == "1"
    assert calls == []


def test_cli_verify_dry_run_uses_command_plan(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    calls: list[object] = []

    def fake_run(*args: object, **kwargs: object) -> int:
        calls.append((args, kwargs))
        return 0

    monkeypatch.setattr("xampler.cli_runtime.run", fake_run)
    assert main(["--json", "--dry-run", "examples", "verify", "r2"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "verify"
    assert payload["surface"] == "r2"
    assert payload["dry_run"] is True
    assert calls == []
