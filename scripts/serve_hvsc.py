#!/usr/bin/env python3
"""Initialize and run the HVSC AI/data example for browser exploration."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "hvsc-24-ai-data-search"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9595)
    args = parser.parse_args()

    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "d1",
            "execute",
            "xampler-hvsc",
            "--local",
            "--file",
            "db_init.sql",
        ],
        cwd=EXAMPLE,
        check=True,
    )

    os.chdir(EXAMPLE)
    os.execvp(
        "uv",
        ["uv", "run", "pywrangler", "dev", "--port", str(args.port), "--local"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
