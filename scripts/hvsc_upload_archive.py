#!/usr/bin/env python3
"""Upload the HVSC archive to a permanent R2 bucket with Wrangler.

Requires Cloudflare auth in Wrangler. This intentionally does not run as part of
normal verification.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "hvsc-24-ai-data-search"
ARCHIVE = ROOT / ".data" / "hvsc" / "84" / "raw" / "HVSC_84-all-of-them.7z"
DEFAULT_KEY = "hvsc/84/raw/HVSC_84-all-of-them.7z"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bucket")
    parser.add_argument("--key", default=DEFAULT_KEY)
    parser.add_argument("--file", type=Path, default=ARCHIVE)
    parser.add_argument("--local", action="store_true", help="Upload to local R2 instead of remote")
    args = parser.parse_args()
    if not args.file.exists():
        raise SystemExit(f"missing archive: {args.file}")
    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "r2",
            "object",
            "put",
            f"{args.bucket}/{args.key}",
            "--file",
            str(args.file),
            "--content-type",
            "application/x-7z-compressed",
            "--local" if args.local else "--remote",
        ],
        check=True,
        cwd=EXAMPLE,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
