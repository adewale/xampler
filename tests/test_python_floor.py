"""The declared Python floor must be the version the checks actually run against.

`requires-python` once said >=3.12 while CI, pyright and ty all pinned 3.13, and the
package could not be imported on 3.12 (`TypeVar(default=...)` is 3.13+). These tests
keep the metadata floor, the type-checker targets and the running interpreter in step.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def declared_floor() -> tuple[int, int]:
    spec = PYPROJECT["project"]["requires-python"]
    match = re.fullmatch(r">=\s*(\d+)\.(\d+)", spec)
    assert match, f"expected a simple '>=X.Y' requires-python, got {spec!r}"
    return int(match.group(1)), int(match.group(2))


def test_running_interpreter_satisfies_declared_floor() -> None:
    assert sys.version_info[:2] >= declared_floor()


def test_type_checkers_target_the_declared_floor() -> None:
    floor = "{}.{}".format(*declared_floor())
    examples_config = json.loads((ROOT / "pyright.examples.json").read_text(encoding="utf-8"))
    assert PYPROJECT["tool"]["pyright"]["pythonVersion"] == floor
    assert examples_config["pythonVersion"] == floor
    assert PYPROJECT["tool"]["ruff"]["target-version"] == "py{}{}".format(*declared_floor())
