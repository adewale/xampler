from __future__ import annotations

import os

from xampler.cli import main


def test_cli_list_and_docs(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["list"]) == 0
    assert "r2" in capsys.readouterr().out

    assert main(["docs", "r2"]) == 0
    assert "docs/api/reference/r2.md" in capsys.readouterr().out


def test_cli_doctor_profile(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setitem(os.environ, "WRANGLER_R2_SQL_AUTH_TOKEN", "token")
    assert main(["doctor", "r2-sql"]) == 0
    output = capsys.readouterr().out
    assert "xc remote prepare r2-sql" in output
    assert "WRANGLER_R2_SQL_AUTH_TOKEN: set" in output
    assert "cost warning" in output
