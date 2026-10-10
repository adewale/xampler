"""Example packaging that the Python Workers toolchain depends on.

Current `workers-py` installs Worker packages with `--no-build` unless the example sets
`[tool.pywrangler] allow-build = true`. The git dependencies (`cfboundary`, `xampler`)
have no prebuilt wheel, so without it `pywrangler dev` fails before the Worker starts.
The local runtime verifier found that; this test catches it without starting a Worker.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIRS = {"node_modules", "python_modules", ".venv", ".venv-workers"}

# With builds allowed, pydantic-core resolves to a PyPI sdist that cannot build for
# Pyodide. Known gap, documented in docs/api/primitive-test-realism.md.
CANNOT_ALLOW_BUILD = {
    "examples/ai-agents/langchain-style-chain",
    "examples/start/fastapi-worker",
}


def test_examples_with_git_dependencies_allow_builds() -> None:
    missing: set[str] = set()
    for pyproject in (ROOT / "examples").rglob("pyproject.toml"):
        if GENERATED_DIRS.intersection(pyproject.parts):
            continue
        config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        dependencies: list[str] = config.get("project", {}).get("dependencies", [])
        allow_build = config.get("tool", {}).get("pywrangler", {}).get("allow-build")
        if any("git+" in dependency for dependency in dependencies) and allow_build is not True:
            missing.add(pyproject.parent.relative_to(ROOT).as_posix())

    assert missing == CANNOT_ALLOW_BUILD
