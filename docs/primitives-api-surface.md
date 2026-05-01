# Cloudflare Primitive API Surface

Last reviewed: 2026-05-01. Scores are out of **10**.

Coverage scores answer: **how much of the Cloudflare primitive's useful API surface does this example demonstrate?**

Pythonic scores answer: **how natural, typed, testable, layered, and honest is our Python-facing API surface?**

Sorted by Pythonic score, highest first.

| Primitive | Example | Coverage | Pythonic API | API surface exposed in this repo | Main missing pieces |
|---|---|---:|---:|---|---|
| R2 object storage | `r2-01` | 8.5 | 9.25 | `R2Bucket`, `R2ObjectRef`, `R2Object`, `R2HttpMetadata`, `R2Range`, `R2Conditional`, `R2ListResult`, `R2MultipartUpload`; `object()`, `read_*`, `write_*`, `exists`, `stat`, `iter_objects`, multipart `async with`, `.raw`. | Presigned URLs/S3 API, public buckets, CORS, lifecycle rules, event notifications. |
| Workers Assets | `assets-06-static-assets` | 7.0 | 8.75 | Direct static asset serving through Wrangler `assets`; Python only handles dynamic route. | More deployment/cache examples. |
| Workers KV | `kv-02-binding` | 7.5 | 8.5 | `KVNamespace`, `KVKey`, `KVListResult`; `key()`, `read_text`, `write_text`, `read_json`, `write_json`, `exists`, `delete`, `list`, `iter_keys`, platform aliases `get_*`/`put_*`. | Metadata returns, cache TTL docs, bulk patterns, stronger list verifier. |
| D1 database | `d1-04-query` | 6.8 | 8.5 | `D1Database`, `D1Statement`, `statement()`, `all`, `one`, `one_as`, typed `Quote`, D1 null conversion. | Migrations, batch/transaction examples, automated local DB setup. |
| Durable Objects | `durable-objects-07-counter` | 6.5 | 8.25 | `Counter`, `CounterNamespace.named()`, named object routing, storage-backed counter. | Typed stub/ref, alarms, transactions, storage SQL, hibernation in isolated example. |
| Workers AI | `workers-ai-09-inference` | 5.5 | 8.25 | `AIService.generate_text()`, `TextGenerationRequest`. | Model catalog helpers, typed responses, image/audio/embedding tasks, verified runtime check. |
| Queues | `queues-16-producer-consumer` | 7.5 | 8.25 | `QueueService`, `QueueJob`, `QueueConsumer`; `send_json`, `send_many`, per-message ack/retry with backoff. | Pull consumer API, dead-letter queues, local `/process-now` verifier, multiple queues. |
| FastAPI / ASGI | `fastapi-03-framework` | 6.0 | 8.0 | Normal `FastAPI` app, ASGI bridge in `Default.fetch`, env access through ASGI scope. | Larger routing, middleware, error handling, package compatibility notes. |
| Cron Triggers | `scheduled-08-cron` | 6.0 | 8.0 | `ScheduledJob.run()`, `scheduled()` handler. | Typed event wrapper, local scheduled verification, persistence/observability example. |
| Binary responses / Pillow | `images-12-generation` | 6.0 | 8.0 | Pillow-generated PNG and binary `Response`. | Query param validation, Cloudflare Images API, caching, R2 output. |
| Service Bindings / RPC | `service-bindings-13-rpc` | 6.0 | 8.0 | Python RPC `highlight_code`, TypeScript client binding. | One-command two-worker verifier, typed request/response models, auth/error patterns. |
| Durable Objects + WebSockets | `durable-objects-15-chatroom` | 7.0 | 8.0 | `ChatRoom`, WebSocketPair, room routing, hibernation API, browser client, message history. | Automated WebSocket verifier, `ChatSession`, persistence across restarts. |
| Vectorize | `vectorize-17-search` | 7.2 | 8.25 | `VectorIndex`, `Vector`, `VectorQuery`, `VectorMatch`, `VectorQueryResult`; `upsert`, `search`, `query`, `get`, `delete`, `describe`; typed query/results. | Metadata index management, `query_by_id`, batching helper, deterministic local verification. |
| Pages | `pages-23-functions` | 5.0 | 8.0 | Static `public/`, file-based Pages Function `functions/api/hello.ts`, Pages mental model. | Python-specific Pages Functions are not supported; more routing/middleware examples. |
| Workflows | `workflows-10-pipeline` | 6.5 | 7.75 | `Pipeline` workflow, `WorkflowService.start`, `status`, named durable steps. | `WorkflowInstance` handle, typed event payloads, verified full status flow. |
| HTMLRewriter | `htmlrewriter-11-opengraph` | 4.5 | 7.75 | `OpenGraphPage` metadata model and executable HTML output. | Real `HTMLRewriter` wrapper and element handlers. |
| Outbound WebSockets | `websockets-14-stream-consumer` | 6.5 | 7.75 | `StreamConsumer` Durable Object, outbound JS WebSocket, alarms, Pyodide proxy notes. | Deterministic fake stream, session wrapper, reconnect state persistence. |
| Browser Rendering | `browser-rendering-18-screenshot` | 5.0 | 7.75 | `BrowserRendering`, `ScreenshotRequest`; REST screenshot endpoint through `fetch`. | Browser binding/Puppeteer or Playwright control, content/PDF/scrape/links/markdown. |
| Email Workers | `email-workers-19-router` | 5.5 | 7.75 | `EmailRouter`, `IncomingEmail`; inspect, reject blocked domains, forward with `X-*` header. | Reply API, SendEmail binding, MIME parsing, deterministic email event verifier. |
| AI Gateway | `ai-gateway-20-universal` | 5.0 | 7.75 | `AIGateway`, `ChatRequest`, `ChatMessage`; OpenAI-compatible chat through gateway. | Caching/rate-limit metadata, dynamic routing/fallbacks, provider key patterns, observability. |
| R2 Data Catalog | `r2-data-catalog-22-iceberg` | 5.0 | 7.75 | `R2DataCatalog`; list namespaces/tables via Iceberg REST API. | PyIceberg client example, table creation, append/read, schema evolution, snapshots. |
| R2 SQL | `r2-sql-21-query` | 4.5 | 7.5 | `R2SqlClient`, `R2SqlQuery`; POST SQL to R2 SQL endpoint. | Schema discovery helpers, result dataclasses, query builder, parameter safety, verification. |
| LangChain/package orchestration | `ai-05-langchain` | 3.0 | 6.75 | `PromptService` boundary only. | Real LangChain-compatible workload or removal/replacement. |

## Aggregate view

- Average coverage: **6.1 / 10**
- Average Pythonic API score: **8.1 / 10**

The API design is generally ahead of the feature coverage. That is intentional for now: the examples establish the Pythonic shape, then each primitive can be made more comprehensive and verified over time.

## API design pattern used across primitives

Each primitive should converge on three layers:

1. **Friendly Python layer** — resource handles and familiar verbs (`read_text`, `write_json`, `exists`, `iter_*`).
2. **Cloudflare platform layer** — the real product vocabulary (`send`, `query`, `upsert`, `status`, metadata/options).
3. **Escape hatch** — `.raw` or explicit low-level clients for unwrapped Workers APIs.
