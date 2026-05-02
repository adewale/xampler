#!/usr/bin/env python3
"""Run the real HVSC dataset pipeline end-to-end.

This downloads the 80 MiB archive, unpacks it, builds a catalog from actual SID
files, optionally uploads archive/catalog to R2, and imports the catalog into D1.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", help="Optional permanent R2 bucket to upload archive/catalog")
    parser.add_argument("--database", default="xampler-hvsc")
    parser.add_argument("--remote-d1", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-upload", action="store_true")
    parser.add_argument("--local-upload", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Catalog build limit; 0 means all files",
    )
    args = parser.parse_args()

    if not args.skip_download:
        run(["uv", "run", "python", "scripts/hvsc_download_unpack.py"])
    build = ["uv", "run", "python", "scripts/hvsc_build_catalog.py"]
    if args.limit:
        build += ["--limit", str(args.limit)]
    run(build)
    if args.bucket and not args.skip_upload:
        local_flag = ["--local"] if args.local_upload else []
        run(["uv", "run", "python", "scripts/hvsc_upload_archive.py", args.bucket, *local_flag])
        run(["uv", "run", "python", "scripts/hvsc_upload_catalog.py", args.bucket, *local_flag])
    import_cmd = [
        "uv",
        "run",
        "python",
        "scripts/hvsc_import_catalog_d1.py",
        "--database",
        args.database,
    ]
    if args.remote_d1:
        import_cmd.append("--remote")
    run(import_cmd)
    return 0


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
