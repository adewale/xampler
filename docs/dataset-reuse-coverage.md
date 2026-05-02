# R2 Dataset Reuse Coverage Plan

Last reviewed: 2026-05-02.

We now treat the user-owned R2 dataset bucket as a shared source of realistic input data. The first dataset is HVSC 84:

```text
hvsc/84/raw/HVSC_84-all-of-them.7z
hvsc/84/catalog/tracks.jsonl
hvsc/84/catalog/composers.jsonl
hvsc/84/catalog/search-documents.jsonl
hvsc/84/catalog/sample-jeroen.jsonl
```

The archive is about 80 MiB. The catalog files are downstream of unpacking the archive and are better suited for D1, Vectorize, Workers AI, R2 SQL, and UI examples.

## Actual score increase already captured

| Example | Primitive/topic | Before bucket/dataset work | Current | Increase |
|---|---|---:|---:|---:|
| `hvsc-24-ai-data-search` | AI/data app coverage | 8.0 | 8.6 | +0.6 |
| `hvsc-24-ai-data-search` | Pythonic API | 8.7 | 9.0 | +0.3 |
| `hvsc-24-ai-data-search` | Test realism | 4.0 | 4.5 | +0.5 |

Why: the complex example now has optional full-archive streaming into R2, archive verification, catalog ingestion, D1 track search, and a real `jeroen` search path.

## Coverage opportunities by primitive

| Primitive | Existing example | Dataset reuse | Coverage now | Coverage after implementation | Gain |
|---|---|---|---:|---:|---:|
| Workers | `workers-01-hello` | Add a dataset health route that reports configured dataset keys and response helpers. | 6.0 | 6.4 | +0.4 |
| R2 | `r2-01` | Use HVSC archive for large-object `head`, range reads, streaming, metadata, and optional copy/delete examples. | 8.5 | 9.2 | +0.7 |
| KV | `kv-02-binding` | Cache dataset version metadata and search UI feature flags. | 8.0 | 8.2 | +0.2 |
| FastAPI | `fastapi-03-framework` | Expose `/datasets/hvsc/search` FastAPI routes over the D1/R2 catalog. | 6.0 | 7.0 | +1.0 |
| D1 | `d1-04-query` | Replace tiny quotes-only data with HVSC tracks/composers sample tables and indexed `composer` queries. | 7.5 | 8.3 | +0.8 |
| Assets | `assets-06-static-assets` | Serve a static HVSC search UI that calls a Worker API. | 7.4 | 7.8 | +0.4 |
| Durable Objects | `durable-objects-07-counter` | Coordinate a per-dataset import progress actor keyed by `hvsc/84`. | 7.0 | 7.7 | +0.7 |
| Cron Triggers | `scheduled-08-cron` | Scheduled dataset freshness check: compare HVSC API version to R2 metadata. | 6.5 | 7.4 | +0.9 |
| Workers AI | `workers-ai-09-inference` | Summarize composer/track metadata from R2 catalog rows. | 6.3 | 7.5 | +1.2 |
| Workflows | `workflows-10-pipeline` | Model archive -> catalog -> D1 -> vector indexing as a real workflow. | 7.2 | 8.3 | +1.1 |
| HTMLRewriter | `htmlrewriter-11-opengraph` | Generate OpenGraph tags for composer/search-result pages from D1 catalog rows. | 5.5 | 6.5 | +1.0 |
| Binary responses | `images-12-generation` | Generate deterministic binary responses for composer/track share-card fixtures. | 6.0 | 7.0 | +1.0 |
| Service Bindings/RPC | `service-bindings-13-rpc` | Python service exposes HVSC search/highlight, TS client consumes it. | 6.0 | 7.1 | +1.1 |
| WebSockets | `websockets-14-stream-consumer` | Stream import progress/events while catalog rows are processed. | 6.5 | 7.2 | +0.7 |
| DO + WebSockets | `durable-objects-15-chatroom` | Add a collaborative HVSC listening/search room seeded from the catalog. | 7.5 | 8.0 | +0.5 |
| Queues | `queues-16-producer-consumer` | Queue jobs reference R2 catalog shards and per-track indexing payloads. | 8.1 | 8.8 | +0.7 |
| Vectorize | `vectorize-17-search` | Embed `search-documents.jsonl` rows and query by composer/title concepts. | 7.8 | 8.8 | +1.0 |
| Browser Rendering | `browser-rendering-18-screenshot` | Screenshot HVSC search results page. | 5.0 | 6.2 | +1.2 |
| Email Workers | `email-workers-19-router` | Email query like `search: jeroen`; Worker returns matching catalog rows. | 5.5 | 6.5 | +1.0 |
| AI Gateway | `ai-gateway-20-universal` | Route HVSC summary prompts through AI Gateway over selected catalog rows. | 5.0 | 6.6 | +1.6 |
| R2 SQL | `r2-sql-21-query` | Query catalog exports once converted to Parquet/Iceberg-friendly format. | 6.5 | 8.0 | +1.5 |
| R2 Data Catalog | `r2-data-catalog-22-iceberg` | Register HVSC tracks as an Iceberg table and list schema/snapshots. | 5.0 | 7.5 | +2.5 |
| Pages | `pages-23-functions` | Pages UI for HVSC search backed by Worker/D1 API. | 6.0 | 7.2 | +1.2 |
| HVSC AI/data app | `hvsc-24-ai-data-search` | Use full generated catalog from R2 and remote Workers AI/Vectorize mode. | 8.6 | 9.3 | +0.7 |

## Highest leverage next implementations

1. **R2**: add large-object archive `head`, `range`, and `stream` routes using the permanent bucket.
2. **D1**: ingest `sample-jeroen.jsonl` or `tracks.jsonl` into a richer D1 search example.
3. **Vectorize + Workers AI**: embed a capped subset of `search-documents.jsonl`.
4. **Workflows + Queues**: turn dataset processing into durable, observable pipeline steps.
5. **R2 SQL + Data Catalog**: convert catalog to Parquet/Iceberg and query it.
6. **Pages/FastAPI/Assets**: put user-facing search UI examples on top of the same dataset.

## Tracking rule

Only increase README scores when the repo contains runnable code and verifier coverage for that increase. This document tracks the projected upside. The README tracks implemented state.
