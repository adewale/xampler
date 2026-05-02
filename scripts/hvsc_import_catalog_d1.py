#!/usr/bin/env python3
"""Import a generated HVSC tracks.jsonl catalog into D1 using Wrangler.

This is the non-fake path for arbitrary composer/title/path search. It imports
rows generated from the unpacked HVSC archive by `scripts/hvsc_build_catalog.py`.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / ".data" / "hvsc" / "84" / "catalog" / "tracks.jsonl"
SCHEMA = ROOT / "examples/full-apps/hvsc-ai-data-search" / "db_init.sql"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--database", default="xampler-hvsc")
    parser.add_argument("--remote", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=500)
    args = parser.parse_args()

    if not args.catalog.exists():
        raise SystemExit(f"missing catalog: {args.catalog}")

    execute_sql(args.database, SCHEMA, remote=args.remote)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, chunk in enumerate(chunks(args.catalog, args.chunk_size), start=1):
            sql_path = tmp_path / f"tracks-{index:04d}.sql"
            write_sql_chunk(sql_path, chunk)
            execute_sql(args.database, sql_path, remote=args.remote)
            print(f"imported chunk {index} ({len(chunk)} rows)")
    return 0


def chunks(path: Path, size: int):
    chunk: list[dict] = []
    with path.open(encoding="utf-8") as catalog:
        for line in catalog:
            if not line.strip():
                continue
            chunk.append(json.loads(line))
            if len(chunk) >= size:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def write_sql_chunk(path: Path, rows: list[dict]) -> None:
    lines = ["BEGIN TRANSACTION;"]
    for row in rows:
        values = [
            row["id"],
            int(row["version"]),
            row["path"],
            row["filename"],
            row.get("title"),
            row.get("composer"),
            row["search_text"],
        ]
        lines.append(
            "INSERT OR REPLACE INTO tracks "
            "(id, version, path, filename, title, composer, search_text) VALUES "
            f"({sql_value(values[0])}, {values[1]}, {sql_value(values[2])}, "
            f"{sql_value(values[3])}, {sql_value(values[4])}, "
            f"{sql_value(values[5])}, {sql_value(values[6])});"
        )
    lines.append("COMMIT;")
    path.write_text("\n".join(lines), encoding="utf-8")


def sql_value(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    return sqlite3.connect(":memory:").execute("SELECT quote(?)", (str(value),)).fetchone()[0]


def execute_sql(database: str, file: Path, *, remote: bool) -> None:
    command = ["uv", "run", "pywrangler", "d1", "execute", database, "--file", str(file)]
    command.append("--remote" if remote else "--local")
    subprocess.run(command, cwd=ROOT / "examples/full-apps/hvsc-ai-data-search", check=True)


if __name__ == "__main__":
    raise SystemExit(main())
