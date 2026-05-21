# Cloudflare Primitive API Surface

Last reviewed: 2026-05-09. Recalibrated after capability/error/CLI hardening. Scores are out of **10**.

Coverage scores answer: **how much of the Cloudflare primitive's useful API surface does this example demonstrate?**

Pythonic scores answer: **how natural, typed, testable, layered, safe, and honest is our Python-facing API surface?** Operation-level capability labels live in [`primitive-test-realism.md`](primitive-test-realism.md): supported, supported with caveat, demo-only, remote-only, unsupported/throws, and not covered.

Sorted by Pythonic score, highest first.

| Primitive | Example | Coverage | Pythonic API | API surface exposed in this repo | Main missing pieces |
|---|---|---:|---:|---|---|
| R2 object storage | `examples/storage-data/r2-object-storage` + `xampler.r2` | 8.8 | 9.4 | Shared `R2Bucket`, `R2ObjectRef`, `R2Object`, `R2HttpMetadata`, `R2Range`, `R2Conditional`, `R2ListResult`, `R2MultipartUpload`; object-handle `read_*`/`write_*`, bucket-level `put_*`/`get_*`, `exists`, `stat`, `iter_objects`, multipart `async with`, `.raw`. | Presigned URLs/S3 API, public buckets, CORS, lifecycle rules, event notifications. |
| AI/data app | `examples/full-apps/hvsc-ai-data-search` | 8.6 | 9.0 | `HvscPipeline`, `HvscRelease`, `Track`, `IngestJob`, `SearchResult`, R2 artifact storage, optional 80 MiB archive streaming/verification, D1 release + track metadata, Queue job, deterministic summarizer/vector search, HVSC sample catalog with Jeroen search. | Remote Workers AI/Vectorize verification, full catalog import from generated JSONL, FastAPI facade. |
| Streaming composition | `examples/streaming/gutenberg-stream-composition` | 8.4 | 9.0 | `ByteStream`, `JsonlReader`, `RecordStream`, `aiter_batches`, `Checkpoint`, AI/agent/WebSocket stream event shapes, Gutenberg R2 golden file, direct R2 object-body ZIP unzip demo, checkpointed D1 line pipeline, full extracted text indexed into D1 FTS with verification queries. | Resumable incremental FTS ingestion and deployed R2/D1 verification. |
| Workers KV | `examples/storage-data/kv-namespace` + `xampler.kv` | 8.2 | 9.0 | Shared `KVNamespace`, `KVKey`, `KVListResult`; `key()`, `read_text`, `write_text`, `read_json`, `write_json`, `exists`, `delete`, `list`, `iter_keys`; verifier covers text, JSON, list, delete. | Metadata returns, cache TTL docs, bulk patterns, deployed namespace verification. |
| D1 database | `examples/storage-data/d1-database` + `xampler.d1` | 7.8 | 9.0 | Shared `D1Database`, `D1Statement`, `statement()`, `all`, `one`, `first`, `one_as`, `execute`, `batch_run`, typed `Quote`, parameter binding, indexed query plan route, D1 null conversion. | Migrations, transaction examples, retry helpers, write/mutation route. |
| Workers Assets | `examples/start/static-assets` | 7.4 | 9.0 | Direct static asset serving through Wrangler `assets`; Python only handles dynamic `/api/status` route; verifier proves static/dynamic separation. | Cache/header assertions, SPA/not-found routing examples. |
| Queues | `examples/state-events/queues-producer-consumer` + `xampler.queues` | 8.2 | 8.9 | Shared `QueueService`, `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, `QueueConsumer`, `QueueEventRecorder`; `send`, `send_json`, `send_many`, per-message ack/retry with backoff; producer and deterministic consumer harness are verified. Durable Object tracking is example-local because it is observability, not a Queue API. | Real local queue delivery, multiple queues, richer DLQ cleanup. |
| Vectorize | `examples/ai-agents/vectorize-search` + `xampler.vectorize` | 8.0 | 8.9 | Shared `VectorIndex`, `Vector`, `VectorQuery`, `VectorMatch`, `VectorQueryResult`; `upsert`, `search`, `query`, `query_by_id`, `get`, `delete`, `describe`; typed query/results, 32-dimensional fixture vectors, deployed real binding verification. | Metadata index management and batching helper. |
| Workers AI | `examples/ai-agents/workers-ai-inference` + `xampler.ai` | 6.5 | 8.8 | Shared `AIService.run`, `generate_text`, `TextGenerationRequest`, `TextGenerationResponse`, deterministic `DemoAIService`; typed text response, raw result escape, prepared deployed AI verification. | Model catalog helpers, image/audio/embedding tasks, response metadata assertions. |
| R2 Data Catalog | `examples/storage-data/r2-data-catalog` + `xampler.r2_data_catalog` | 7.3 | 8.7 | Shared `R2DataCatalog`, `DemoR2DataCatalog`, `CatalogNamespace`, `TableRef`; list namespaces/tables plus temporary create-list-delete lifecycle via Iceberg REST API, fixture verifier, bucket/catalog prepare path, deployed-secret remote path. | PyIceberg client example, append/read, schema evolution, snapshots. |
| R2 SQL | `examples/storage-data/r2-sql` + `xampler.r2_sql` | 7.0 | 8.7 | Shared `R2SqlClient`, `R2SqlQuery`, `R2SqlResult`, read-only/single-table safety checks, automatic `LIMIT`, `explain`, deterministic demo client, documented R2 SQL REST endpoint, deployed-secret remote path, seeded table `SELECT` verification. | Schema discovery helpers, richer query builder, row-content assertions. |
| Agents SDK | `examples/ai-agents/agents-sdk-tools` | 6.8 | 8.7 | `AgentMessage`, `AgentToolCall`, `AgentRunResult`, `WeatherTool`, `DemoAgent`, `AgentSession`, Durable Object session routing. | Direct Cloudflare Agents SDK interop as Python support matures, streaming agent responses, human-in-the-loop state. |
| Durable Objects + WebSockets | `examples/state-events/durable-object-chatroom` | 7.5 | 8.6 | `ChatRoom`, WebSocketPair, room routing, hibernation API, browser client, persisted message history, deterministic room-state verifier. | True automated WebSocket client broadcast verifier and `ChatSession` abstraction. |
| Workflows | `examples/state-events/workflows-pipeline` | 7.2 | 8.6 | `Pipeline` workflow, `WorkflowService`, `WorkflowInstance`, `WorkflowStart`, `WorkflowStatus`, named durable steps, deterministic verifier. | Real Workflow runtime status verification and typed event payloads. |
| Durable Objects | `examples/state-events/durable-object-counter` | 7.0 | 8.6 | `Counter`, `CounterNamespace.named()`, typed `CounterRef`, named object routing, storage-backed counter, named-object isolation verification. | Concurrent increments, alarms, transactions, storage SQL, hibernation in isolated example. |
| Browser Rendering | `examples/network-edge/browser-rendering-screenshot` + `xampler.browser_rendering` | 6.8 | 8.5 | Shared `BrowserRendering`, `DemoBrowserRendering`, `ScreenshotRequest`, `ScreenshotResult`; REST screenshot/content/PDF/scrape endpoints, local demo, deployed-secret remote preparation path. | Browser binding/Puppeteer or Playwright control from Python, links/markdown extraction. |
| AI Gateway | `examples/ai-agents/ai-gateway-chat` | 6.6 | 8.5 | Shared `AIGateway`, `DemoAIGateway`, `ChatRequest`, `ChatMessage`, `ChatResponse`; OpenAI-compatible chat through gateway and deterministic local gateway shape. | Caching/rate-limit metadata, dynamic routing/fallbacks, provider key patterns, observability. |
| Cron Triggers | `examples/state-events/cron-trigger` | 6.5 | 8.5 | `ScheduledEventInfo`, `ScheduledRunResult`, `ScheduledJob.run()`, `scheduled()` handler, local scheduled endpoint verification. | Persistence/observability example. |
| Hyperdrive | `examples/storage-data/hyperdrive-postgres` | 6.5 | 8.5 | `HyperdriveConfig`, `PostgresQuery`, `PostgresResult`, `HyperdrivePostgres`, `DemoPostgres`; local verifier and deployed config route. | Real Postgres client wiring, transactions, pooling notes, remote Hyperdrive verifier. |
| Pages | `examples/start/pages-functions` | 6.0 | 8.4 | Static `public/`, file-based Pages Function `functions/api/hello.ts`, Pages mental model, Pages dev verifier. | Python-specific Pages Functions are not supported; more routing/middleware examples. |
| Service Bindings / RPC | `examples/network-edge/service-bindings-rpc` | 6.8 | 8.3 | Python RPC `highlight_code`, TypeScript client binding, local provider verifier. | Full two-worker process verifier, auth/error patterns. |
| Email Workers | `examples/network-edge/email-worker-router` | 6.5 | 8.3 | `EmailRouter`, `IncomingEmail`, `EmailDecision`; inspect, reject, forward, deterministic HTTP policy verifier. | Reply API, SendEmail binding, richer MIME parsing, deployed Email Routing test. |
| HTMLRewriter | `examples/network-edge/htmlrewriter-opengraph` | 5.5 | 8.3 | `OpenGraphPage` metadata model, `OpenGraphRewriter` transformation wrapper, escaped metadata, executable HTML output. | Replace internals with real Python-native `HTMLRewriter` when available. |
| Outbound WebSockets | `examples/network-edge/outbound-websocket-consumer` | 7.0 | 8.2 | `StreamConsumer` Durable Object, outbound JS WebSocket, alarms, Pyodide proxy notes, deterministic `/demo/status`. | Richer fake stream messages, persisted reconnect state. |
| Binary responses | `examples/streaming/binary-response` | 6.0 | 8.2 | Dependency-free deterministic PNG bytes and binary `Response`; verifier asserts PNG signature and content type. | Query param validation, Cloudflare Images API, caching, R2 output. |
| LangChain/package orchestration | `examples/ai-agents/langchain-style-chain` | 6.2 | 8.1 | `PromptInput`, `PromptOutput`, `PromptTemplate`, `DemoModel`, `PromptChain`, `PromptService`; dependency-light LCEL-style Runnable shape verified locally. | Add real LangChain package compatibility when Pyodide support is sufficient. |
| FastAPI / ASGI | `examples/start/fastapi-worker` | 6.0 | 8.0 | Normal `FastAPI` app, ASGI bridge in `Default.fetch`, env access through ASGI scope. | Larger routing, middleware, error handling, package compatibility notes. |

## Aggregate view

- Average coverage: **7.1 / 10**
- Average Pythonic API score: **8.6 / 10**

The API design is generally ahead of the feature coverage. That is intentional for now: the examples establish the Pythonic shape, then each primitive can be made more comprehensive and verified over time.

## API design pattern used across primitives

Each primitive should converge on five visible contracts:

1. **Friendly Python layer** — resource handles and familiar verbs (`read_text`, `write_json`, `exists`, `iter_*`).
2. **Cloudflare platform layer** — the real product vocabulary (`send`, `query`, `upsert`, `status`, metadata/options).
3. **Capability honesty** — docs say supported, caveated, demo-only, remote-only, unsupported/throws, or not covered for important operations.
4. **Safe failure behavior** — missing values, unsupported options, auth failures, conflicts, and provider errors have predictable Python/route/tool behavior.
5. **Escape hatch** — `.raw` or explicit low-level clients for unwrapped Workers APIs.
