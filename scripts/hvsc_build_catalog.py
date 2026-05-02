#!/usr/bin/env python3
"""Build JSONL catalogs from an unpacked HVSC tree."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data" / "hvsc" / "84"
UNPACKED = DATA / "unpacked"
CATALOG = DATA / "catalog"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unpacked", type=Path, default=UNPACKED)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--limit", type=int, default=0, help="0 means no limit")
    parser.add_argument("--shard-size", type=int, default=500)
    args = parser.parse_args()

    args.catalog.mkdir(parents=True, exist_ok=True)
    tracks = list(iter_tracks(args.unpacked, args.limit))
    write_jsonl(args.catalog / "tracks.jsonl", tracks)
    write_jsonl(args.catalog / "search-documents.jsonl", tracks)
    composers = Counter(track["composer"] for track in tracks if track["composer"])
    write_jsonl(
        args.catalog / "composers.jsonl",
        [{"composer": name, "track_count": count} for name, count in composers.most_common()],
    )
    sample = [track for track in tracks if "jeroen" in track["search_text"].lower()][:100]
    write_jsonl(args.catalog / "sample-jeroen.jsonl", sample)
    write_shards(args.catalog / "shards", tracks, args.shard_size)
    print(f"wrote {len(tracks):,} tracks to {args.catalog}")
    return 0


def iter_tracks(root: Path, limit: int):
    for count, path in enumerate(sorted(root.rglob("*.sid")), start=1):
        rel = path.relative_to(root).as_posix()
        composer = infer_composer(rel)
        title = path.stem.replace("_", " ")
        yield {
            "id": "hvsc:84:" + rel.lower().replace("/", ":"),
            "version": 84,
            "path": rel,
            "filename": path.name,
            "title": title,
            "composer": composer,
            "search_text": f"{composer} {title} Commodore 64 C64 SID {rel}",
        }
        if limit and count >= limit:
            break


def infer_composer(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0].upper() == "MUSICIANS":
        return parts[2].replace("_", " ")
    return ""


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_shards(path: Path, rows: list[dict], shard_size: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for old in path.glob("*.jsonl"):
        old.unlink()
    for index, start in enumerate(range(0, len(rows), shard_size)):
        write_jsonl(path / f"{index:04d}.jsonl", rows[start : start + shard_size])


if __name__ == "__main__":
    raise SystemExit(main())
