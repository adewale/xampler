#!/usr/bin/env python3
"""Upload generated HVSC catalog JSONL files to R2."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "hvsc-24-ai-data-search"
CATALOG = ROOT / ".data" / "hvsc" / "84" / "catalog"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bucket")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--prefix", default="hvsc/84/catalog")
    args = parser.parse_args()
    for path in sorted(args.catalog.glob("*.jsonl")):
        key = f"{args.prefix}/{path.name}"
        subprocess.run(
            [
                "uv",
                "run",
                "pywrangler",
                "r2",
                "object",
                "put",
                f"{args.bucket}/{key}",
                "--file",
                str(path),
                "--content-type",
                "application/x-ndjson",
            ],
            check=True,
            cwd=EXAMPLE,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
