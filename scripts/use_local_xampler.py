#!/usr/bin/env python3
"""Temporarily point example dependencies at the local xampler checkout.

Most examples depend on ``xampler @ git+https://github.com/adewale/xampler@main`` so
normal users get a reproducible GitHub dependency. Maintainers editing the shared
``xampler/`` package and examples together can run this script to replace that
with a local ``file://`` dependency, then restore before committing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_DEP = '    "xampler @ git+https://github.com/adewale/xampler@main",'


def local_dep() -> str:
    return f'    "xampler @ file://{ROOT.as_posix()}",'


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
    changed = [path for path in example_pyprojects() if rewrite(path, restore=args.restore)]
    action = "restored" if args.restore else "linked"
    for path in changed:
        print(f"{action}: {path.relative_to(ROOT)}")
    if not changed:
        print("no example pyproject files needed changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
