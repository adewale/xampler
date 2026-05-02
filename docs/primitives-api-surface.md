# Cloudflare Primitive API Surface

Last reviewed: 2026-05-02. Scores are out of **10**.

Coverage scores answer: **how much of the Cloudflare primitive's useful API surface does this example demonstrate?**

Pythonic scores answer: **how natural, typed, testable, layered, and honest is our Python-facing API surface?**

Sorted by Pythonic score, highest first.

| Primitive | Example | Coverage | Pythonic API | API surface exposed in this repo | Main missing pieces |
|---|---|---:|---:|---|---|
| R2 object storage | `r2-01` | 8.5 | 9.25 | `R2Bucket`, `R2ObjectRef`, `R2Object`, `R2HttpMetadata`, `R2Range`, `R2Conditional`, `R2ListResult`, `R2MultipartUpload`; `object()`, `read_*`, `write_*`, `exists`, `stat`, `iter_objects`, multipart `async with`, `.raw`. | Presigned URLs/S3 API, public buckets, CORS, lifecycle rules, event notifications. |
| Workers Assets | `assets-06-static-assets` | 7.4 | 9.0 | Direct static asset serving through Wrangler `assets`; Python only handles dynamic `/api/status` route; verifier proves static/dynamic separation. | Cache/header assertions, SPA/not-found routing examples. |
| Workers KV | `kv-02-binding` | 8.0 | 8.8 | `KVNamespace`, `KVKey`, `KVListResult`; `key()`, `read_text`, `write_text`, `read_json`, `write_json`, `exists`, `delete`, `list`, `iter_keys`, platform aliases `get_*`/`put_*`; verifier covers text, JSON, list, delete. | Metadata returns, cache TTL docs, bulk patterns, deployed namespace verification. |
| D1 database | `d1-04-query` | 7.5 | 8.9 | `D1Database`, `D1Statement`, `statement()`, `all`, `one`, `one_as`, typed `Quote`, parameter binding, indexed query plan route, D1 null conversion. | Migrations, batch/transaction examples, retry helpers, write/mutation route. |
| Durable Objects | `durable-objects-07-counter` | 7.0 | 8.6 | `Counter`, `CounterNamespace.named()`, typed `CounterRef`, named object routing, storage-backed counter, named-object isolation verification. | Concurrent increments, alarms, transactions, storage SQL, hibernation in isolated example. |
| Workers AI | `workers-ai-09-inference` | 6.3 | 8.7 | `AIService.run`, `generate_text`, `TextGenerationRequest`, `TextGenerationResponse`, deterministic `DemoAIService`; typed text response and raw result escape. | Model catalog helpers, image/audio/embedding tasks, deployed AI verification. |
| Queues | `queues-16-producer-consumer` | 8.1 | 8.7 | `QueueService`, `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, `QueueConsumer`; `send`, `send_json`, `send_many`, per-message ack/retry with backoff; producer and deterministic consumer harness are verified. | Real local queue delivery, dead-letter queues, multiple queues. |
| FastAPI / ASGI | `fastapi-03-framework` | 6.0 | 8.0 | Normal `FastAPI` app, ASGI bridge in `Default.fetch`, env access through ASGI scope. | Larger routing, middleware, error handling, package compatibility notes. |
| Cron Triggers | `scheduled-08-cron` | 6.5 | 8.5 | `ScheduledEventInfo`, `ScheduledRunResult`, `ScheduledJob.run()`, `scheduled()` handler, local scheduled endpoint verification. | Persistence/observability example. |
| Binary responses | `images-12-generation` | 6.0 | 8.2 | Dependency-free deterministic PNG bytes and binary `Response`; verifier asserts PNG signature and content type. | Query param validation, Cloudflare Images API, caching, R2 output. |
| Service Bindings / RPC | `service-bindings-13-rpc` | 6.8 | 8.3 | Python RPC `highlight_code`, TypeScript client binding, local provider verifier. | Full two-worker process verifier, auth/error patterns. |
| Durable Objects + WebSockets | `durable-objects-15-chatroom` | 7.5 | 8.5 | `ChatRoom`, WebSocketPair, room routing, hibernation API, browser client, persisted message history, deterministic room-state verifier. | True automated WebSocket client broadcast verifier and `ChatSession` abstraction. |
| Vectorize | `vectorize-17-search` | 7.8 | 8.7 | `VectorIndex`, `Vector`, `VectorQuery`, `VectorMatch`, `VectorQueryResult`; `upsert`, `search`, `query`, `query_by_id`, `get`, `delete`, `describe`; typed query/results and dimension validation. | Metadata index management, batching helper, remote Vectorize verification. |
| Pages | `pages-23-functions` | 6.0 | 8.4 | Static `public/`, file-based Pages Function `functions/api/hello.ts`, Pages mental model, Pages dev verifier. | Python-specific Pages Functions are not supported; more routing/middleware examples. |
| Workflows | `workflows-10-pipeline` | 7.2 | 8.5 | `Pipeline` workflow, `WorkflowService`, `WorkflowInstance`, `WorkflowStart`, `WorkflowStatus`, named durable steps, deterministic verifier. | Real Workflow runtime status verification and typed event payloads. |
| HTMLRewriter | `htmlrewriter-11-opengraph` | 5.5 | 8.3 | `OpenGraphPage` metadata model, `OpenGraphRewriter` transformation wrapper, escaped metadata, executable HTML output. | Replace internals with real Python-native `HTMLRewriter` when available. |
| Outbound WebSockets | `websockets-14-stream-consumer` | 7.0 | 8.2 | `StreamConsumer` Durable Object, outbound JS WebSocket, alarms, Pyodide proxy notes, deterministic `/demo/status`. | Richer fake stream messages, persisted reconnect state. |
| Browser Rendering | `browser-rendering-18-screenshot` | 6.2 | 8.2 | `BrowserRendering`, `DemoBrowserRendering`, `ScreenshotRequest`, `ScreenshotResult`; REST screenshot endpoint and local demo. | Browser binding/Puppeteer or Playwright control, content/PDF/scrape/links/markdown. |
| Email Workers | `email-workers-19-router` | 6.5 | 8.3 | `EmailRouter`, `IncomingEmail`, `EmailDecision`; inspect, reject, forward, deterministic HTTP policy verifier. | Reply API, SendEmail binding, richer MIME parsing, deployed Email Routing test. |
| AI Gateway | `ai-gateway-20-universal` | 6.5 | 8.4 | `AIGateway`, `DemoAIGateway`, `ChatRequest`, `ChatMessage`, `ChatChoice`; OpenAI-compatible chat through gateway and deterministic local gateway shape. | Caching/rate-limit metadata, dynamic routing/fallbacks, provider key patterns, observability. |
| R2 Data Catalog | `r2-data-catalog-22-iceberg` | 6.8 | 8.3 | `R2DataCatalog`, `DemoR2DataCatalog`, `Namespace`, `TableRef`; list namespaces/tables via Iceberg REST API and fixture verifier. | PyIceberg client example, table creation, append/read, schema evolution, snapshots. |
| R2 SQL | `r2-sql-21-query` | 6.5 | 8.4 | `R2SqlClient`, `R2SqlQuery`, `R2SqlResult`, read-only/single-table safety checks, automatic `LIMIT`, `explain`, deterministic demo client. | Schema discovery helpers, richer query builder, real R2 SQL verification. |
| AI/data app | `hvsc-24-ai-data-search` | 8.6 | 9.0 | `HvscPipeline`, `HvscRelease`, `Track`, `IngestJob`, `SearchResult`, R2 artifact storage, optional 80 MiB archive streaming/verification, D1 release + track metadata, Queue job, deterministic summarizer/vector search, HVSC sample catalog with Jeroen search. | Remote Workers AI/Vectorize verification, full catalog import from generated JSONL, FastAPI facade. |
| LangChain/package orchestration | `ai-05-langchain` | 6.2 | 8.1 | `PromptInput`, `PromptOutput`, `PromptTemplate`, `DemoModel`, `PromptChain`, `PromptService`; dependency-light LCEL-style Runnable shape verified locally. | Add real LangChain package compatibility when Pyodide support is sufficient. |
| Hyperdrive | `hyperdrive-25-postgres` | 6.5 | 8.4 | `HyperdriveConfig`, `PostgresQuery`, `PostgresResult`, `HyperdrivePostgres`, `DemoPostgres`; local verifier and deployed config route. | Real Postgres client wiring, transactions, pooling notes, remote Hyperdrive verifier. |
| Agents SDK | `agents-26-sdk` | 6.8 | 8.6 | `AgentMessage`, `AgentToolCall`, `AgentRunResult`, `WeatherTool`, `DemoAgent`, `AgentSession`, Durable Object session routing. | Direct Cloudflare Agents SDK interop as Python support matures, streaming agent responses, human-in-the-loop state. |
| Streaming composition | `streaming-27-gutenberg` | 7.2 | 8.8 | `ByteStream`, `JsonlReader`, `RecordStream`, `aiter_batches`, `StreamCheckpoint`, AI/agent/WebSocket stream event shapes, Gutenberg R2 golden file. | Lift streaming helpers into shared package and wire real R2 streams into the pipeline. |

## Aggregate view

- Average coverage: **6.2 / 10**
- Average Pythonic API score: **8.1 / 10**

The API design is generally ahead of the feature coverage. That is intentional for now: the examples establish the Pythonic shape, then each primitive can be made more comprehensive and verified over time.

## API design pattern used across primitives

Each primitive should converge on three layers:

1. **Friendly Python layer** — resource handles and familiar verbs (`read_text`, `write_json`, `exists`, `iter_*`).
2. **Cloudflare platform layer** — the real product vocabulary (`send`, `query`, `upsert`, `status`, metadata/options).
3. **Escape hatch** — `.raw` or explicit low-level clients for unwrapped Workers APIs.
