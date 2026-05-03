# Xampler library surface

Xampler is a Python library with examples that prove the APIs run in Python Workers.

## Import map

| Module | Status | Primary imports |
|---|---|---|
| `xampler.r2` | Stable | `R2Bucket`, `R2ObjectRef`, `R2HttpMetadata`, `R2Range`, `R2Conditional` |
| `xampler.d1` | Stable | `D1Database`, `D1Statement` |
| `xampler.kv` | Stable | `KVNamespace`, `KVKey`, `KVListResult` |
| `xampler.streaming` | Stable | `ByteStream`, `JsonlReader`, `aiter_batches`, `StreamCheckpoint` |
| `xampler.response` | Stable | `jsonable`, `error_payload` |
| `xampler.status` | Stable | `Progress`, `Checkpoint`, `BatchResult` |
| `xampler.cloudflare` | Stable base | `CloudflareService`, `ResourceRef`, `RestClient` |
| `xampler.queues` | Beta | `QueueService`, `QueueJob`, `QueueConsumer`, `QueueBatchResult` |
| `xampler.vectorize` | Beta | `VectorIndex`, `Vector`, `VectorQuery`, `DemoVectorIndex` |
| `xampler.ai` | Beta | `AIService`, `TextGenerationRequest`, `DemoAIService` |
| `xampler.browser_rendering` | Experimental | `BrowserRendering`, `ScreenshotRequest` |
| `xampler.r2_sql` | Experimental | `R2SqlClient`, `R2SqlQuery`, `DemoR2SqlClient` |
| `xampler.r2_data_catalog` | Experimental | `R2DataCatalog`, `CatalogNamespace`, `TableRef` |

## Stability meanings

- **Stable**: intended for users to import; covered by strict `pyright`, unit tests, and executable examples.
- **Beta**: intended for users to try; API may still change as remote verification deepens.
- **Experimental**: product/auth behavior is still evolving or token-backed verification is not regular yet.

## Design contract

All product modules should preserve these rules:

1. Keep Cloudflare product vocabulary visible.
2. Wrap active bindings or clients in service/client classes.
3. Use dataclasses for request/result/options shapes.
4. Use `async for` for streams and pagination where applicable.
5. Keep `.raw` available for platform escape hatches.
6. Keep demo transports explicit as `Demo*`, never hidden as if real products ran locally.

## What stays in examples

Route handlers, HTML, verifier-only endpoints, fixtures, UI state, and app-specific pipeline logic stay in `examples/`. Library modules own reusable product API shape.
