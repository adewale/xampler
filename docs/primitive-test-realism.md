# Primitive Test Realism Matrix

Last reviewed: 2026-05-01.

This document tracks how realistically each Cloudflare primitive example is tested. It separates three things that are easy to conflate:

1. **Static validation** — Python code parses, lints, and unit tests pass.
2. **Local runtime verification** — `uv run pywrangler dev` is started and HTTP/WebSocket/email/queue behavior is exercised. Pages is the exception because Pages Functions are not Python Workers.
3. **Cloudflare resource realism** — the example uses the real primitive semantics, not just an in-memory stand-in.

## Realism levels

| Level | Meaning |
|---:|---|
| 0 | Not tested. |
| 1 | Static only: lint/import/unit tests, no Worker runtime. |
| 2 | Worker starts locally, but only a shallow route/health check is verified. |
| 3 | Local runtime exercises the primitive with local Wrangler/Miniflare semantics. |
| 4 | Local runtime exercises the primitive including realistic data and edge cases. |
| 5 | Deployed or remote-binding verification against real Cloudflare infrastructure. |

## Matrix

| Primitive | Example | Realism | Current verification | What is actually tested | Main gap to next level |
|---|---|---:|---|---|---|
| Workers request/response | `examples/start/hello-worker` | 3 | `uv run python scripts/verify_examples.py examples/start/hello-worker` | Starts Python Worker locally and checks HTTP response body. | Add multiple methods/headers/error response checks. |
| R2 object storage | `examples/storage-data/r2-object-storage` | 4 | `uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage` | Starts Worker locally, writes/reads text, uploads `fixtures/BreakingThe35.jpeg`, streams it back, byte-compares download. | Remote-binding/deployed R2 verification; multipart verification. |
| Workers KV | `examples/storage-data/kv-namespace` | 4 | `uv run python scripts/verify_examples.py examples/storage-data/kv-namespace` | Starts Worker locally, writes/reads text, writes/reads JSON, lists keys, deletes a key, and verifies a missing-key 404. | Verify TTL/expiration behavior and deployed KV namespace. |
| FastAPI / ASGI | `examples/start/fastapi-worker` | 3 | `uv run python scripts/verify_examples.py examples/start/fastapi-worker` | Starts Worker locally through the ASGI bridge and verifies `/` plus `/items/python`. | Add `/env` verification and a template/dependency route like the official example. |
| D1 database | `examples/storage-data/d1-database` | 4 | `uv run python scripts/verify_examples.py examples/storage-data/d1-database` | Initializes local D1 with `db_init.sql`, creates an index, runs `PRAGMA optimize`, starts the Worker, verifies a seeded row, verifies bound query, and checks an `EXPLAIN QUERY PLAN` route for index use. | Add write/query mutation route, retry guidance, and remote/deployed D1 verification. |
| LangChain/package orchestration | `examples/ai-agents/langchain-style-chain` | 3 | `uv run python scripts/verify_examples.py examples/ai-agents/langchain-style-chain` | Starts Worker locally and verifies a dependency-light LCEL-style Runnable chain with typed input/output. | Add real LangChain package compatibility when Pyodide support is sufficient. |
| Workers Assets | `examples/start/static-assets` | 4 | `uv run python scripts/verify_examples.py examples/start/static-assets` | Starts Worker locally, verifies the static asset is served by Workers Assets instead of Python, and verifies a dynamic Python route under `/api/status`, proving static/dynamic routing separation. | Add cache/header assertions and SPA/not-found routing examples. |
| Durable Objects | `examples/state-events/durable-object-counter` | 4 | `uv run python scripts/verify_examples.py examples/state-events/durable-object-counter` | Starts Worker locally, resets two named counters, increments them independently, and verifies persisted state plus named-object isolation. | Verify concurrent increments, alarms, and WebSocket hibernation patterns. |
| Cron Triggers | `examples/state-events/cron-trigger` | 4 | `uv run python scripts/verify_examples.py examples/state-events/cron-trigger` | Starts Worker locally, verifies health route, hits Wrangler's local `/cdn-cgi/handler/scheduled` endpoint, and keeps job logic typed/testable via dataclasses. | Persist an observable side effect and verify it through storage/log capture. |
| Workers AI | `examples/ai-agents/workers-ai-inference` | 4 | `uv run python scripts/verify_examples.py examples/ai-agents/workers-ai-inference` | Starts Worker locally and verifies typed request/response handling through deterministic `/demo`; real `/` keeps the Workers AI binding path. | Remote/deployed AI verification with an account token and deterministic prompt. |
| Workflows | `examples/state-events/workflows-pipeline` | 4 | `uv run python scripts/verify_examples.py examples/state-events/workflows-pipeline` | Starts Worker locally and verifies typed `WorkflowStart`/`WorkflowStatus` through deterministic `/demo/start` and `/demo/status/<id>`; real `/start` keeps Workflow binding path. | Verify real workflow instance creation/status in local or deployed runtime. |
| Queues | `examples/state-events/queues-producer-consumer` | 4 | `uv run python scripts/verify_examples.py examples/state-events/queues-producer-consumer` | Starts Worker locally, verifies producer enqueue, and exercises the same consumer ack/retry path through a deterministic local batch harness. | Verify real local queue delivery and dead-letter behavior. |
| Vectorize | `examples/ai-agents/vectorize-search` | 4 | `uv run python scripts/verify_examples.py examples/ai-agents/vectorize-search` | Starts Worker locally and verifies deterministic vector search with dimension validation, typed matches, metadata, and result ordering; real routes keep Vectorize binding paths. | Remote index verification for `/upsert`, `/query`, and `query_by_id`. |
| HTMLRewriter | `examples/network-edge/htmlrewriter-opengraph` | 4 | `uv run python scripts/verify_examples.py examples/network-edge/htmlrewriter-opengraph` | Starts Worker locally and verifies escaped OpenGraph metadata inserted by a typed transformation wrapper. | Swap wrapper internals to a real Python-native `HTMLRewriter` when available. |
| Binary responses | `examples/streaming/binary-response` | 4 | `uv run python scripts/verify_examples.py examples/streaming/binary-response` | Starts Worker locally and verifies content-type plus PNG signature for deterministic dependency-free PNG bytes. | Add query validation, cache headers, and optional R2 output. |
| Service bindings / RPC | `examples/network-edge/service-bindings-rpc` | 3 | `uv run python scripts/verify_examples.py examples/network-edge/service-bindings-rpc/py` | Starts the Python RPC provider locally and verifies highlighted HTML through the same method the TS service binding calls. | Full one-command two-process verifier for Python provider + TS consumer. |
| Outbound WebSockets | `examples/network-edge/outbound-websocket-consumer` | 3 | `uv run python scripts/verify_examples.py examples/network-edge/outbound-websocket-consumer` | Starts Worker locally and verifies deterministic stream status; real `/status` keeps the outbound Jetstream path. | Deterministic fake WebSocket server and persisted reconnect state verification. |
| Durable Objects + WebSockets | `examples/state-events/durable-object-chatroom` | 4 | `uv run python scripts/verify_examples.py examples/state-events/durable-object-chatroom` | Starts Worker locally, serves chat UI, routes to a room Durable Object, sends a deterministic message through the same room state path, and verifies history. | Add a true automated WebSocket client broadcast test. |
| Browser Rendering | `examples/network-edge/browser-rendering-screenshot` | 3 | `uv run python scripts/verify_examples.py examples/network-edge/browser-rendering-screenshot` | Starts Worker locally and verifies typed screenshot request/result through deterministic `/demo`; real route keeps REST API path. | Env-gated real Browser Rendering screenshot/PDF/content verification. |
| Email Workers | `examples/network-edge/email-worker-router` | 3 | `uv run python scripts/verify_examples.py examples/network-edge/email-worker-router` | Starts Worker locally and verifies deterministic email routing policy with typed `IncomingEmail` and `EmailDecision`. | Local email event harness or deployed Email Routing test. |
| AI Gateway | `examples/ai-agents/ai-gateway-chat` | 3 | `uv run python scripts/verify_examples.py examples/ai-agents/ai-gateway-chat` | Starts Worker locally and verifies OpenAI-compatible gateway response shape through deterministic `/demo`; real route keeps gateway path. | Env-gated real gateway/provider verification with metadata/cache assertions. |
| R2 SQL | `examples/storage-data/r2-sql` | 4 | `uv run python scripts/verify_examples.py examples/storage-data/r2-sql` | Starts Worker locally and verifies safe read-only query shaping, automatic `LIMIT`, and `EXPLAIN` via deterministic `/demo`; real route keeps REST API path. | Verify against real R2 SQL endpoint with `SHOW DATABASES` and sample query. |
| R2 Data Catalog | `examples/storage-data/r2-data-catalog` | 3 | `uv run python scripts/verify_examples.py examples/storage-data/r2-data-catalog` | Starts Worker locally and verifies Iceberg namespace/table-shaped responses through deterministic `/demo`; real routes keep REST catalog path. | PyIceberg client example, table creation/append/read, remote catalog verification. |
| Pages | `examples/start/pages-functions` | 4 | `uv run python scripts/verify_examples.py examples/start/pages-functions` | Starts `uv run pywrangler pages dev public`, verifies static `/`, and verifies file-routed `/api/hello?name=Python`. | Add middleware/not-found examples and deployed Pages verification. |
| AI/data app | `examples/full-apps/hvsc-ai-data-search` | 4.5 | `uv run python scripts/verify_examples.py examples/full-apps/hvsc-ai-data-search` | Initializes local D1, ingests HVSC release metadata and sample track catalog, writes raw JSON/catalog data to R2, stores searchable release/track metadata in D1, sends a queue job, verifies `jeroen` track search, and includes optional 80 MiB archive streaming/verification to local R2. | Remote verification for permanent R2 bucket, Workers AI, and Vectorize; full generated catalog import. |
| Hyperdrive | `examples/storage-data/hyperdrive-postgres` | 3 | `uv run python scripts/verify_examples.py examples/storage-data/hyperdrive-postgres` | Starts Worker locally and verifies typed Postgres query/result shape through deterministic `/demo`; `/config` and `/query` keep Hyperdrive binding vocabulary. | Real Postgres client wiring and env-gated Hyperdrive verification. |
| Agents SDK | `examples/ai-agents/agents-sdk-tools` | 3 | `uv run python scripts/verify_examples.py examples/ai-agents/agents-sdk-tools` | Starts Worker locally and verifies typed agent messages, tool calls, final result, and Durable Object session routing. | Direct Agents SDK interop, streaming responses, persisted human-in-the-loop state. |
| Streaming composition | `examples/streaming/gutenberg-stream-composition` | 3 | `uv run python scripts/verify_examples.py examples/streaming/gutenberg-stream-composition` | Starts Worker locally and verifies stream-to-stream composition plus AI/agent/WebSocket event streams. | Wire direct R2 byte stream from the Gutenberg golden file into the local pipeline. |

## Current realism summary

| Level | Count | Examples |
|---:|---:|---|
| 4 | 15 | `examples/storage-data/r2-object-storage`, `examples/storage-data/kv-namespace`, `examples/storage-data/d1-database`, `examples/state-events/durable-object-counter`, `examples/state-events/cron-trigger`, `examples/state-events/queues-producer-consumer`, `examples/ai-agents/workers-ai-inference`, `examples/state-events/workflows-pipeline`, `examples/ai-agents/vectorize-search`, `examples/state-events/durable-object-chatroom`, `examples/start/pages-functions`, `examples/storage-data/r2-sql`, `examples/full-apps/hvsc-ai-data-search`, `examples/network-edge/htmlrewriter-opengraph`, `examples/streaming/binary-response` |
| 3 | 11 | `examples/start/hello-worker`, `examples/start/fastapi-worker`, `examples/ai-agents/langchain-style-chain`, `examples/network-edge/service-bindings-rpc`, `examples/network-edge/outbound-websocket-consumer`, `examples/network-edge/browser-rendering-screenshot`, `examples/network-edge/email-worker-router`, `examples/ai-agents/ai-gateway-chat`, `examples/storage-data/r2-data-catalog`, `examples/storage-data/hyperdrive-postgres`, `examples/ai-agents/agents-sdk-tools` |
| 2 | 0 | — |
| 1 | 0 | — |
| 0 | 0 | — |

## Highest-priority testing work

1. **Promote level-3 examples to level 4**: add richer deterministic local harnesses, not just single endpoint checks.
2. **Add env-gated remote profiles** for Browser Rendering, AI Gateway, R2 SQL, R2 Data Catalog, Hyperdrive, Agents, and Email Routing.
3. **Bring Queues, Chatroom WebSockets, and Service Bindings to level 4/5** with true multi-process or WebSocket clients.
4. **Keep R2 at level 4+**: the JPEG byte-for-byte upload/download fixture is the current gold standard for realistic local verification.

## Verification commands currently known to pass

```bash
uv run python scripts/verify_examples.py examples/start/hello-worker
uv run python scripts/verify_examples.py examples/storage-data/r2-object-storage
uv run python scripts/verify_examples.py examples/storage-data/kv-namespace
uv run python scripts/verify_examples.py examples/state-events/durable-object-counter
uv run python scripts/verify_examples.py examples/start/fastapi-worker
uv run python scripts/verify_examples.py examples/storage-data/d1-database
uv run python scripts/verify_examples.py examples/start/static-assets
uv run python scripts/verify_examples.py examples/state-events/queues-producer-consumer
uv run python scripts/verify_examples.py examples/streaming/binary-response
uv run python scripts/verify_examples.py examples/network-edge/htmlrewriter-opengraph
uv run python scripts/verify_examples.py examples/state-events/cron-trigger
uv run python scripts/verify_examples.py examples/ai-agents/workers-ai-inference
uv run python scripts/verify_examples.py examples/state-events/workflows-pipeline
uv run python scripts/verify_examples.py examples/ai-agents/vectorize-search
uv run python scripts/verify_examples.py examples/state-events/durable-object-chatroom
uv run python scripts/verify_examples.py examples/start/pages-functions
uv run python scripts/verify_examples.py examples/storage-data/r2-sql
uv run python scripts/verify_examples.py examples/full-apps/hvsc-ai-data-search
uv run python scripts/verify_examples.py examples/ai-agents/langchain-style-chain
uv run python scripts/verify_examples.py examples/network-edge/service-bindings-rpc/py
uv run python scripts/verify_examples.py examples/network-edge/outbound-websocket-consumer
uv run python scripts/verify_examples.py examples/network-edge/browser-rendering-screenshot
uv run python scripts/verify_examples.py examples/network-edge/email-worker-router
uv run python scripts/verify_examples.py examples/ai-agents/ai-gateway-chat
uv run python scripts/verify_examples.py examples/storage-data/r2-data-catalog
uv run python scripts/verify_examples.py examples/storage-data/hyperdrive-postgres
uv run python scripts/verify_examples.py examples/ai-agents/agents-sdk-tools
```
