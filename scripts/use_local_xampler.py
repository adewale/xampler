#!/usr/bin/env python3
"""Temporarily point example dependencies at a locally built xampler wheel.

Most examples depend on ``xampler @ git+https://github.com/adewale/xampler@main`` so
normal users get a reproducible GitHub dependency. Maintainers editing the shared
``xampler/`` package and examples together can run this script to build a local
wheel, replace the GitHub dependency with that wheel, then restore before
committing.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_DEP = '    "xampler @ git+https://github.com/adewale/xampler@main",'


def wheel_path() -> Path:
    return ROOT / "dist" / "xampler-0.1.0-py3-none-any.whl"


def local_dep() -> str:
    return f'    "xampler @ file://{wheel_path().as_posix()}",'


def example_pyprojects() -> list[Path]:
    return sorted(path for path in (ROOT / "examples").rglob("pyproject.toml"))


def rewrite(path: Path, *, restore: bool) -> bool:
    text = path.read_text()
    source = local_dep() if restore else GIT_DEP
    target = GIT_DEP if restore else local_dep()
    if source not in text:
        return False
    path.write_text(text.replace(source, target))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore examples to the GitHub xampler dependency before committing.",
    )
    args = parser.parse_args()
    if not args.restore:
        subprocess.run(["uv", "build", "--wheel"], cwd=ROOT, check=True)
    changed = [path for path in example_pyprojects() if rewrite(path, restore=args.restore)]
    action = "restored" if args.restore else "linked"
    for path in changed:
        print(f"{action}: {path.relative_to(ROOT)}")
    if not changed:
        print("no example pyproject files needed changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
