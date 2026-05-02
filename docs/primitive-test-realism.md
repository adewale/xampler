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
| Workers request/response | `workers-01-hello` | 3 | `uv run python scripts/verify_examples.py workers-01-hello` | Starts Python Worker locally and checks HTTP response body. | Add multiple methods/headers/error response checks. |
| R2 object storage | `r2-01` | 4 | `uv run python scripts/verify_examples.py r2-01` | Starts Worker locally, writes/reads text, uploads `fixtures/BreakingThe35.jpeg`, streams it back, byte-compares download. | Remote-binding/deployed R2 verification; multipart verification. |
| Workers KV | `kv-02-binding` | 4 | `uv run python scripts/verify_examples.py kv-02-binding` | Starts Worker locally, writes/reads text, writes/reads JSON, lists keys, deletes a key, and verifies a missing-key 404. | Verify TTL/expiration behavior and deployed KV namespace. |
| FastAPI / ASGI | `fastapi-03-framework` | 3 | `uv run python scripts/verify_examples.py fastapi-03-framework` | Starts Worker locally through the ASGI bridge and verifies `/` plus `/items/python`. | Add `/env` verification and a template/dependency route like the official example. |
| D1 database | `d1-04-query` | 4 | `uv run python scripts/verify_examples.py d1-04-query` | Initializes local D1 with `db_init.sql`, creates an index, runs `PRAGMA optimize`, starts the Worker, verifies a seeded row, verifies bound query, and checks an `EXPLAIN QUERY PLAN` route for index use. | Add write/query mutation route, retry guidance, and remote/deployed D1 verification. |
| LangChain/package orchestration | `ai-05-langchain` | 3 | `uv run python scripts/verify_examples.py ai-05-langchain` | Starts Worker locally and verifies a dependency-light LCEL-style Runnable chain with typed input/output. | Add real LangChain package compatibility when Pyodide support is sufficient. |
| Workers Assets | `assets-06-static-assets` | 4 | `uv run python scripts/verify_examples.py assets-06-static-assets` | Starts Worker locally, verifies the static asset is served by Workers Assets instead of Python, and verifies a dynamic Python route under `/api/status`, proving static/dynamic routing separation. | Add cache/header assertions and SPA/not-found routing examples. |
| Durable Objects | `durable-objects-07-counter` | 4 | `uv run python scripts/verify_examples.py durable-objects-07-counter` | Starts Worker locally, resets two named counters, increments them independently, and verifies persisted state plus named-object isolation. | Verify concurrent increments, alarms, and WebSocket hibernation patterns. |
| Cron Triggers | `scheduled-08-cron` | 4 | `uv run python scripts/verify_examples.py scheduled-08-cron` | Starts Worker locally, verifies health route, hits Wrangler's local `/cdn-cgi/handler/scheduled` endpoint, and keeps job logic typed/testable via dataclasses. | Persist an observable side effect and verify it through storage/log capture. |
| Workers AI | `workers-ai-09-inference` | 4 | `uv run python scripts/verify_examples.py workers-ai-09-inference` | Starts Worker locally and verifies typed request/response handling through deterministic `/demo`; real `/` keeps the Workers AI binding path. | Remote/deployed AI verification with an account token and deterministic prompt. |
| Workflows | `workflows-10-pipeline` | 4 | `uv run python scripts/verify_examples.py workflows-10-pipeline` | Starts Worker locally and verifies typed `WorkflowStart`/`WorkflowStatus` through deterministic `/demo/start` and `/demo/status/<id>`; real `/start` keeps Workflow binding path. | Verify real workflow instance creation/status in local or deployed runtime. |
| Queues | `queues-16-producer-consumer` | 4 | `uv run python scripts/verify_examples.py queues-16-producer-consumer` | Starts Worker locally, verifies producer enqueue, and exercises the same consumer ack/retry path through a deterministic local batch harness. | Verify real local queue delivery and dead-letter behavior. |
| Vectorize | `vectorize-17-search` | 4 | `uv run python scripts/verify_examples.py vectorize-17-search` | Starts Worker locally and verifies deterministic vector search with dimension validation, typed matches, metadata, and result ordering; real routes keep Vectorize binding paths. | Remote index verification for `/upsert`, `/query`, and `query_by_id`. |
| HTMLRewriter | `htmlrewriter-11-opengraph` | 4 | `uv run python scripts/verify_examples.py htmlrewriter-11-opengraph` | Starts Worker locally and verifies escaped OpenGraph metadata inserted by a typed transformation wrapper. | Swap wrapper internals to a real Python-native `HTMLRewriter` when available. |
| Binary responses | `images-12-generation` | 4 | `uv run python scripts/verify_examples.py images-12-generation` | Starts Worker locally and verifies content-type plus PNG signature for deterministic dependency-free PNG bytes. | Add query validation, cache headers, and optional R2 output. |
| Service bindings / RPC | `service-bindings-13-rpc` | 3 | `uv run python scripts/verify_examples.py service-bindings-13-rpc-py` | Starts the Python RPC provider locally and verifies highlighted HTML through the same method the TS service binding calls. | Full one-command two-process verifier for Python provider + TS consumer. |
| Outbound WebSockets | `websockets-14-stream-consumer` | 3 | `uv run python scripts/verify_examples.py websockets-14-stream-consumer` | Starts Worker locally and verifies deterministic stream status; real `/status` keeps the outbound Jetstream path. | Deterministic fake WebSocket server and persisted reconnect state verification. |
| Durable Objects + WebSockets | `durable-objects-15-chatroom` | 4 | `uv run python scripts/verify_examples.py durable-objects-15-chatroom` | Starts Worker locally, serves chat UI, routes to a room Durable Object, sends a deterministic message through the same room state path, and verifies history. | Add a true automated WebSocket client broadcast test. |
| Browser Rendering | `browser-rendering-18-screenshot` | 3 | `uv run python scripts/verify_examples.py browser-rendering-18-screenshot` | Starts Worker locally and verifies typed screenshot request/result through deterministic `/demo`; real route keeps REST API path. | Env-gated real Browser Rendering screenshot/PDF/content verification. |
| Email Workers | `email-workers-19-router` | 3 | `uv run python scripts/verify_examples.py email-workers-19-router` | Starts Worker locally and verifies deterministic email routing policy with typed `IncomingEmail` and `EmailDecision`. | Local email event harness or deployed Email Routing test. |
| AI Gateway | `ai-gateway-20-universal` | 3 | `uv run python scripts/verify_examples.py ai-gateway-20-universal` | Starts Worker locally and verifies OpenAI-compatible gateway response shape through deterministic `/demo`; real route keeps gateway path. | Env-gated real gateway/provider verification with metadata/cache assertions. |
| R2 SQL | `r2-sql-21-query` | 4 | `uv run python scripts/verify_examples.py r2-sql-21-query` | Starts Worker locally and verifies safe read-only query shaping, automatic `LIMIT`, and `EXPLAIN` via deterministic `/demo`; real route keeps REST API path. | Verify against real R2 SQL endpoint with `SHOW DATABASES` and sample query. |
| R2 Data Catalog | `r2-data-catalog-22-iceberg` | 3 | `uv run python scripts/verify_examples.py r2-data-catalog-22-iceberg` | Starts Worker locally and verifies Iceberg namespace/table-shaped responses through deterministic `/demo`; real routes keep REST catalog path. | PyIceberg client example, table creation/append/read, remote catalog verification. |
| Pages | `pages-23-functions` | 4 | `uv run python scripts/verify_examples.py pages-23-functions` | Starts `uv run pywrangler pages dev public`, verifies static `/`, and verifies file-routed `/api/hello?name=Python`. | Add middleware/not-found examples and deployed Pages verification. |
| AI/data app | `hvsc-24-ai-data-search` | 4.5 | `uv run python scripts/verify_examples.py hvsc-24-ai-data-search` | Initializes local D1, ingests HVSC release metadata and sample track catalog, writes raw JSON/catalog data to R2, stores searchable release/track metadata in D1, sends a queue job, verifies `jeroen` track search, and includes optional 80 MiB archive streaming/verification to local R2. | Remote verification for permanent R2 bucket, Workers AI, and Vectorize; full generated catalog import. |
| Hyperdrive | `hyperdrive-25-postgres` | 3 | `uv run python scripts/verify_examples.py hyperdrive-25-postgres` | Starts Worker locally and verifies typed Postgres query/result shape through deterministic `/demo`; `/config` and `/query` keep Hyperdrive binding vocabulary. | Real Postgres client wiring and env-gated Hyperdrive verification. |
| Agents SDK | `agents-26-sdk` | 3 | `uv run python scripts/verify_examples.py agents-26-sdk` | Starts Worker locally and verifies typed agent messages, tool calls, final result, and Durable Object session routing. | Direct Agents SDK interop, streaming responses, persisted human-in-the-loop state. |
| Streaming composition | `streaming-27-gutenberg` | 3 | `uv run python scripts/verify_examples.py streaming-27-gutenberg` | Starts Worker locally and verifies stream-to-stream composition plus AI/agent/WebSocket event streams. | Wire direct R2 byte stream from the Gutenberg golden file into the local pipeline. |

## Current realism summary

| Level | Count | Examples |
|---:|---:|---|
| 4 | 15 | `r2-01`, `kv-02-binding`, `d1-04-query`, `durable-objects-07-counter`, `scheduled-08-cron`, `queues-16-producer-consumer`, `workers-ai-09-inference`, `workflows-10-pipeline`, `vectorize-17-search`, `durable-objects-15-chatroom`, `pages-23-functions`, `r2-sql-21-query`, `hvsc-24-ai-data-search`, `htmlrewriter-11-opengraph`, `images-12-generation` |
| 3 | 11 | `workers-01-hello`, `fastapi-03-framework`, `ai-05-langchain`, `service-bindings-13-rpc`, `websockets-14-stream-consumer`, `browser-rendering-18-screenshot`, `email-workers-19-router`, `ai-gateway-20-universal`, `r2-data-catalog-22-iceberg`, `hyperdrive-25-postgres`, `agents-26-sdk` |
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
uv run python scripts/verify_examples.py workers-01-hello
uv run python scripts/verify_examples.py r2-01
uv run python scripts/verify_examples.py kv-02-binding
uv run python scripts/verify_examples.py durable-objects-07-counter
uv run python scripts/verify_examples.py fastapi-03-framework
uv run python scripts/verify_examples.py d1-04-query
uv run python scripts/verify_examples.py assets-06-static-assets
uv run python scripts/verify_examples.py queues-16-producer-consumer
uv run python scripts/verify_examples.py images-12-generation
uv run python scripts/verify_examples.py htmlrewriter-11-opengraph
uv run python scripts/verify_examples.py scheduled-08-cron
uv run python scripts/verify_examples.py workers-ai-09-inference
uv run python scripts/verify_examples.py workflows-10-pipeline
uv run python scripts/verify_examples.py vectorize-17-search
uv run python scripts/verify_examples.py durable-objects-15-chatroom
uv run python scripts/verify_examples.py pages-23-functions
uv run python scripts/verify_examples.py r2-sql-21-query
uv run python scripts/verify_examples.py hvsc-24-ai-data-search
uv run python scripts/verify_examples.py ai-05-langchain
uv run python scripts/verify_examples.py service-bindings-13-rpc-py
uv run python scripts/verify_examples.py websockets-14-stream-consumer
uv run python scripts/verify_examples.py browser-rendering-18-screenshot
uv run python scripts/verify_examples.py email-workers-19-router
uv run python scripts/verify_examples.py ai-gateway-20-universal
uv run python scripts/verify_examples.py r2-data-catalog-22-iceberg
uv run python scripts/verify_examples.py hyperdrive-25-postgres
uv run python scripts/verify_examples.py agents-26-sdk
```
