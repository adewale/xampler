#!/usr/bin/env python3
"""Download and unpack the HVSC archive into .data/hvsc/84.

Uses Python's streaming HTTP download. Extraction uses py7zr when installed, or
falls back to a system `7z` executable.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import urllib.request
from pathlib import Path

HVSC_URL = "https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z"
HVSC_SIZE = 83_748_140
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data" / "hvsc" / "84"
ARCHIVE = DATA / "raw" / "HVSC_84-all-of-them.7z"
UNPACKED = DATA / "unpacked"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=HVSC_URL)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-extract", action="store_true")
    args = parser.parse_args()

    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if args.force or not ARCHIVE.exists():
        download(args.url, ARCHIVE)
    verify_size(ARCHIVE)
    if not args.no_extract:
        extract(ARCHIVE, UNPACKED)
    return 0


def download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response, destination.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
            print(f"downloaded {out.tell():,} bytes", end="\r")
    print(f"downloaded {destination} ({destination.stat().st_size:,} bytes)")


def verify_size(path: Path) -> None:
    size = path.stat().st_size
    if size != HVSC_SIZE:
        raise SystemExit(f"expected {HVSC_SIZE:,} bytes, got {size:,}")
    print(f"verified archive size: {size:,} bytes")


def extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    try:
        import py7zr  # type: ignore[import-not-found]

        with py7zr.SevenZipFile(archive) as zf:
            zf.extractall(destination)
        return
    except ImportError:
        pass

    seven_zip = shutil.which("7z") or shutil.which("7zz")
    if not seven_zip:
        raise SystemExit("Install py7zr or 7z/7zz to extract the archive")
    subprocess.run([seven_zip, "x", str(archive), f"-o{destination}", "-y"], check=True)


if __name__ == "__main__":
    raise SystemExit(main())
