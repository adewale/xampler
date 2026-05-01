# API Surface Review

Last reviewed: 2026-05-01.

After raising the Workers AI, Vectorize, Pages, Durable Objects + WebSockets, Workflows, and R2 SQL examples, the repeated API shape is stronger: service wrappers own platform bindings, dataclasses describe inputs/results, deterministic demo services make local verification possible when Cloudflare account resources are required, and real routes keep the official binding/API vocabulary visible.

## Lesson from `hvsc-24-ai-data-search`

The complex HVSC example made one iteration rule clearer: individual primitives should keep improving toward composability. The useful surface is not just `R2Bucket`, `D1Database`, `QueueService`, `AIService`, or `VectorIndex` in isolation; it is whether those wrappers can be stitched together into a real pipeline without the Worker entrypoint becoming glue-code soup.

Concrete lessons now feeding back into the smaller examples:

- service wrappers need small, typed results that can be passed to the next primitive;
- deterministic `/demo` or fixture routes are essential for account-backed AI/vector services;
- D1 setup belongs in verifiers, not README-only instructions;
- queue messages should be dataclasses, not anonymous dictionaries;
- R2 object keys should be explicit data-contract fields in jobs/results;
- examples should document where they use real Cloudflare bindings and where they use a local deterministic substitute.

## Potential improvements across all examples

| Area | Current pattern | Improvement |
|---|---|---|
| Shared responses | Many examples define local response helpers or use `Response.json` directly. | Add a tiny shared example helper for `text_response`, `json_response`, error responses, and content-type assertions. |
| Deterministic demo modes | Account-backed products now use `/demo` routes. | Standardize route naming and document that `/demo` verifies API shape while `/` or product routes use real bindings. |
| Error handling | Some wrappers raise platform errors directly. | Add typed exception classes such as `CloudflareBindingError`, `RetryableCloudflareError`, and product-specific validation errors. |
| Retry/backoff | Queues and docs mention retry; D1/DO still need helpers. | Add reusable `retry_with_backoff()` for D1 writes and Durable Object stub recreation. |
| `.raw` escape hatch | Present strongly in R2, less explicit elsewhere. | Add `.raw` to service/result handles consistently where a platform object exists. |
| Validation | Vectorize and R2 SQL now validate key constraints. | Add similar validation for request body sizes, image dimensions, model names, and workflow payloads. |
| Test realism | Many examples now have local verification. | Add remote/deployed verification profiles for account-backed products (`--remote` or env-gated tests). |

## Product-specific next API improvements

| Primitive | Next API improvement |
|---|---|
| Workers AI | Add model-specific namespaces such as `ai.text.generate(...)`, `ai.embeddings.create(...)`, and typed model catalog helpers. |
| Vectorize | Add `VectorBatch`, `upsert_batches()`, metadata-index docs, and `query_by_id()` route coverage. |
| Pages | Add middleware example, `_routes.json`/routing notes, and a Pages-specific verifier profile. |
| Durable Objects + WebSockets | Add `ChatSession` dataclass, true WebSocket client verifier, and retry/backoff stub wrapper. |
| Workflows | Add typed workflow payload/event dataclasses and real status polling helper with timeout. |
| R2 SQL | Add safe query-builder presets: `select(columns).from_table(table).where_time_range(...).limit(...)`; add `EXPLAIN` route for real API. |
| D1 | Add write route with retry/backoff, transaction/batch examples, and migration helpers. |
| KV | Add TTL/expiration verification and metadata/cache TTL wrappers. |
| R2 | Runtime-verify multipart upload and add presigned URL/Boto3 companion example. |
| Queues | Verify real local queue delivery and dead-letter behavior. |

## Design rule reinforced

Every product should expose three layers:

1. Friendly Python surface for common work.
2. Cloudflare platform vocabulary for docs parity.
3. `.raw` or low-level escape hatch for newly released platform features.
