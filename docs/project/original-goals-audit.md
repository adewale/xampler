# Audit Against Original Goals

Last reviewed: 2026-05-02.

## Summary

Xampler now substantially meets the original direction: it is a GitHub-hosted collection of executable Python Workers examples, covers a broad set of Cloudflare Developer Platform primitives, uses Pythonic wrappers around bindings, distinguishes real verification from demo seams, and includes realistic shared datasets in R2.

The biggest remaining gaps are remote/account-backed verification, wiring direct R2 streams into more end-to-end pipelines, missing Cache/Analytics/Images product examples, and reducing per-example wrapper duplication into shared typed helpers only after APIs stabilize. See [`gaps-explained.md`](gaps-explained.md) for details.

## Goal-by-goal assessment

| Original goal | Status | Evidence | Remaining gap |
|---|---|---|---|
| GitHub-hosted collection of Pythonic executable Cloudflare Python Workers examples | Met | Examples live under `examples/` and are verified through `scripts/verify_examples.py`. | Keep examples green after reorg. |
| Cover Cloudflare primitives | Mostly met | Workers, R2, KV, D1, Assets, DO, Cron, AI, Workflows, Queues, Vectorize, Pages, Browser Rendering, Email, AI Gateway, R2 SQL, R2 Data Catalog, Hyperdrive, Agents, streaming composition. | Still missing Analytics Engine, Cache API direct example, Turnstile, Rate Limiting, Stream, Calls, Pub/Sub, Workers for Platforms, Tail Workers. |
| Pythonic API surface | Met and improving | Service wrappers, resource handles, dataclasses, typed results, `.raw`, shared `xampler.streaming`, `pyright` strict for shared package. | Lift stable wrappers into `xampler/` gradually; add more Protocol/NewType/Annotated typing. |
| Test realism scoring | Met | `docs/api/primitive-test-realism.md`; README no-lies and demo-seams sections. | More level-4/5 remote checks for account-backed products. |
| Scoring out of 10/10/5 | Met | README primitive metrics and API/test docs. | Keep synchronized after changes. |
| Product/primitive-first naming | Superseded | We intentionally moved away from numbering/product-first flat folders to user-journey grouping. | New structure should stabilize before more docs churn. |
| R2 JPEG upload/download of `BreakingThe35.jpeg` | Met | R2 verifier uploads/streams/byte-compares fixture. | None. |
| Prefer `uv run pywrangler` over npm/npx | Met | Example scripts and docs use `uv run pywrangler`; npm is hidden tooling. | Keep package scripts consistent. |
| Large datasets not committed | Met | `.data/` ignored; HVSC/Gutenberg are in R2, not Git. | Periodically audit generated artifacts. |
| Permanent R2 bucket for datasets | Met | `xampler-datasets` contains HVSC and Gutenberg golden files. | Document object inventory as it grows. |
| Realistic complex AI/data example | Met | `examples/full-apps/hvsc-ai-data-search`. | AI/Vectorize remain deterministic seams locally. |
| Interactive browser flows for complex examples | Met | HVSC browser flow has run-all, progress, search UX. | Add less flicker and better resumability if full import restarts. |
| Avoid fake arbitrary search | Met | HVSC arbitrary search requires/imports real catalog shards. | Keep demo seams explicitly labeled. |
| Add Gutenberg/Shakespeare complex data source | Met | Gutenberg zip uploaded to R2; streaming example has `/zip-demo` that reads the R2 object body stream and unzips the real Gutenberg archive. | Python `zipfile` still buffers because ZIP central directories require seeking. |
| Ground references in Cloudflare docs | Met | `docs/runtime/cloudflare-doc-links.md`; every example README has direct Cloudflare docs links. | Keep links current as docs move. |

## Current golden files

| File | R2 key | Size |
|---|---|---:|
| HVSC 84 archive | `hvsc/84/raw/HVSC_84-all-of-them.7z` | 83,748,140 bytes |
| HVSC 84 track catalog | `hvsc/84/catalog/tracks.jsonl` | 19,071,559 bytes |
| Gutenberg Shakespeare zip | `gutenberg/100/raw/pg100-h.zip` | 2,793,586 bytes |

## What is strongest

- R2 is the no-lies gold standard: text, binary JPEG upload, streaming download, byte comparison.
- D1/KV/Assets/Durable Objects/Cron/Pages are credible local primitive examples.
- HVSC proves multi-primitive composition and honest setup-dependent search.
- The docs now clearly distinguish real examples from deterministic demo seams.

## What is weakest

- Account-backed products often verify only local demo shape, not real Cloudflare remote behavior.
- Streaming helpers are shared, but most primitive wrappers do not yet consume them.
- Direct Cloudflare Images product coverage is still missing; binary response is not Images.
- Folder reorg is clearer but new enough that external links and habits may lag.

## Remaining gaps explained briefly

| Gap | Meaning | Next move |
|---|---|---|
| Remote verification for account-backed products | Local demo transports prove wrapper shape, not real Browser Rendering/AI Gateway/Vectorize/etc. behavior. | Add `--remote` profiles that require credentials and assert product-specific metadata. |
| End-to-end R2 stream pipelines | `/zip-demo` reads the real R2 object body and unzips it, while `/demo` remains a compact sample-text pipeline. | Feed extracted Gutenberg records into the same checkpoint/batch pipeline. |
| Missing Cache/Analytics/Images examples | Common production products are not represented as first-class examples. | Add direct Cache API, Workers Analytics Engine, and Cloudflare Images examples. |
| Wrapper duplication | Examples repeat service/dataclass/status/demo patterns locally. | Lift only stable boring helpers into `xampler/`; keep product hero logic local. |

## Next priorities

1. Add env-gated remote verification profiles for Browser Rendering, AI Gateway, R2 SQL, R2 Data Catalog, Hyperdrive, Workers AI, Vectorize, Agents, Service Bindings, WebSockets, and Queues/DLQ.
2. Add a true non-seekable archive streaming example if a suitable format/library is chosen.
3. Add direct Cache API and Analytics Engine examples.
4. Add Cloudflare Images product example separate from binary response.
5. Continue lifting stable shared types/helpers into `xampler/` with strict pyright coverage.
