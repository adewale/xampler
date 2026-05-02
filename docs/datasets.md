# Shared datasets

Last reviewed: 2026-05-02.

Xampler can use a permanent R2 bucket as a shared data lake for realistic examples. The first dataset is the High Voltage SID Collection (HVSC) release archive.

## Recommended bucket layout

Use a bucket you own, for example:

```text
xampler-datasets
```

Recommended object layout:

```text
hvsc/84/raw/HVSC_84-all-of-them.7z
hvsc/84/metadata/version.json
hvsc/84/catalog/tracks.jsonl
hvsc/84/catalog/composers.jsonl
hvsc/84/catalog/search-documents.jsonl
hvsc/84/catalog/sample-jeroen.jsonl
```

The full archive is currently:

```text
URL:  https://boswme.home.xs4all.nl/HVSC/HVSC_84-all-of-them.7z
Size: 83,748,140 bytes, about 79.9 MiB
```

## Local preparation

Download and unpack:

```bash
uv run python scripts/hvsc_download_unpack.py
```

Build catalogs from the unpacked tree:

```bash
uv run python scripts/hvsc_build_catalog.py --shard-size 500
```

Upload the raw archive to your R2 bucket:

```bash
uv run python scripts/hvsc_upload_archive.py xampler-datasets
```

Upload generated catalogs:

```bash
uv run python scripts/hvsc_upload_catalog.py xampler-datasets
```

These commands require Wrangler to be authenticated for your Cloudflare account. Uploads target remote Cloudflare R2 by default; add `--local` to the upload commands only when you intentionally want to seed Wrangler's local R2 store.

## How examples reuse the bucket

| Example | Reuse |
|---|---|
| `hvsc-24-ai-data-search` | Source archive, sample catalog, D1 search rows, queue indexing jobs, future Workers AI/Vectorize embeddings. |
| `r2-01` | Large object `head`, range, stream, metadata, and multipart comparison. |
| `d1-04-query` | Richer track/composer metadata instead of tiny quotes. |
| `queues-16-producer-consumer` | Queue jobs that reference R2 catalog keys and offsets. |
| `workers-ai-09-inference` | Summarize selected composers/tracks. |
| `vectorize-17-search` | Embed and search track metadata. |
| `r2-sql-21-query` | Query catalog exports when converted to Parquet/Iceberg-compatible data. |
| `r2-data-catalog-22-iceberg` | Catalog HVSC track metadata as an Iceberg table. |

## Cost posture

Default verifiers use small fixtures and deterministic local seams. Full archive download, R2 upload, Workers AI embedding, Vectorize upsert, and R2 SQL/Data Catalog verification should be explicit opt-in steps.
