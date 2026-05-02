# Cloudflare Primitive API Surface Pythonic Scores

Last reviewed: 2026-05-02. Scores are out of **10** and use [`pythonic-rubric.md`](pythonic-rubric.md).

This scores the **API surface we currently expose in the examples**, not Cloudflare's underlying JavaScript APIs.

| Cloudflare primitive / surface | Example | Pythonic score | API surface summary | Main gaps |
|---|---|---:|---|---|
| Workers request/response | `workers-01-hello` | 8.0 | Thin `WorkerEntrypoint`, localized response helper. | Shared response module; richer request parsing helper. |
| R2 object storage | `r2-01` | 9.25 | `R2Bucket`, `R2ObjectRef`, typed metadata/options, `read_*`/`write_*`, `iter_objects`, multipart `async with`, `.raw`. | More route tests; full object-handle docs for every advanced option. |
| Workers KV | `kv-02-binding` | 8.8 | `KVNamespace`, `KVKey`, text/JSON helpers, `exists`, `delete`, `list`, `iter_keys`; verifier covers text, JSON, list, delete. | Metadata/cache/expiration result modeling; deployed namespace verification. |
| FastAPI / ASGI on Workers | `fastapi-03-framework` | 8.0 | Ordinary FastAPI app plus small ASGI adapter in `fetch`. | More Pyodide/package compatibility guidance. |
| D1 database | `d1-04-query` | 8.9 | `D1Database`, `D1Statement`, `statement`, `all`, `one`, `one_as`, typed row dataclass, parameter binding, indexed query plan route, D1 null conversion. | Migrations helper, transactions/batches, retry helpers. |
| Python package / LangChain boundary | `ai-05-langchain` | 8.1 | Typed LCEL-style prompt chain with `PromptInput`, `PromptOutput`, `PromptChain`, service boundary, and local verifier. | Add real LangChain package compatibility when Pyodide support is sufficient. |
| Workers Assets | `assets-06-static-assets` | 9.0 | Teaches bypassing Python for static assets; dynamic `/api/status` route remains tiny and verified separately. | Cache/header assertions and SPA/not-found routing examples. |
| Durable Objects | `durable-objects-07-counter` | 8.6 | Named Durable Object counter, namespace wrapper, typed `CounterRef`, verified reset/increment/read across isolated names. | Concurrent increment checks; storage wrapper. |
| Cron triggers | `scheduled-08-cron` | 8.5 | `ScheduledEventInfo`, `ScheduledRunResult`, `ScheduledJob` service object and scheduled handler. | Persisted side-effect verification. |
| Workers AI | `workers-ai-09-inference` | 8.7 | `AIService`, typed request dataclass, native dict response, deterministic local verifier. | Model-specific helpers; remote AI runtime check. |
| Queues | `queues-16-producer-consumer` | 8.7 | `QueueService`, `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, explicit ack/retry handling, and deterministic consumer harness. | Real queue delivery verifier; dead-letter queue example. |
| Workflows | `workflows-10-pipeline` | 8.5 | Workflow entrypoint, `WorkflowService.start/status`, durable steps, deterministic status verifier. | Real Workflow runtime status verification; richer typed event payloads. |
| HTMLRewriter | `htmlrewriter-11-opengraph` | 8.3 | Metadata dataclass, escaped transformation wrapper, and executable HTML response shape. | Real Python-native `HTMLRewriter` wrapper with element handlers when available. |
| Binary responses | `images-12-generation` | 8.2 | Dependency-free PNG bytes and binary response with content-type and PNG signature verification. | Typed query params, validation, cache/R2 integration. |
| Service bindings / RPC | `service-bindings-13-rpc` | 8.3 | Python RPC method, TS client service binding, and local provider verifier. | Full two-worker verifier; typed request/response dataclasses. |
| Outbound WebSockets | `websockets-14-stream-consumer` | 8.2 | Durable Object-owned outbound socket, alarms, Pyodide `create_proxy` boundary, deterministic status verifier. | Deterministic fake stream messages; higher-level session object. |
| Durable Objects + WebSockets | `durable-objects-15-chatroom` | 8.5 | Room-per-Durable-Object, browser client, WebSocket hibernation API, persisted message history, deterministic room verifier. | Automated WebSocket broadcast verifier; `ChatSession` abstraction. |
| Browser Rendering | `browser-rendering-18-screenshot` | 8.2 | `ScreenshotRequest`, `ScreenshotResult`, REST client, deterministic demo transport. | Content/PDF/scrape helpers and remote verifier. |
| Email Workers | `email-workers-19-router` | 8.3 | `IncomingEmail`, `EmailDecision`, routing policy, HTTP fixture verifier. | Reply/SendEmail/MIME helpers and deployed routing verifier. |
| AI Gateway | `ai-gateway-20-universal` | 8.4 | OpenAI-compatible `ChatRequest`, `ChatMessage`, `ChatChoice`, gateway and demo transports. | Caching/rate-limit metadata and remote verifier. |
| R2 Data Catalog | `r2-data-catalog-22-iceberg` | 8.3 | `Namespace`, `TableRef`, Iceberg REST client, deterministic catalog fixture. | PyIceberg create/append/read and remote verifier. |
| Hyperdrive | `hyperdrive-25-postgres` | 8.4 | `HyperdriveConfig`, `PostgresQuery`, `PostgresResult`, production/demo client split. | Real Postgres client wiring and remote verifier. |
| Agents SDK | `agents-26-sdk` | 8.6 | Typed agent messages, tool calls, run results, deterministic tools, Durable Object session routing. | Streaming responses and direct Agents SDK interop as Python support matures. |
| Streaming composition | `streaming-27-gutenberg` | 8.8 | Typed byte/text/line streams, JSONL reader, batches, checkpoints, AI/agent/WebSocket event streams. | Lift helpers into a shared package and use real R2 body streams. |

## Current average

Current average across these API surfaces: **8.5 / 10**.

## Highest-scoring surfaces

1. **R2 — 9.25/10**: best layered API: friendly object handles, platform vocabulary, typed options, iteration, context manager lifecycle, escape hatch.
2. **Workers Assets — 8.9/10**: Pythonic because it avoids unnecessary Python work.
3. **KV — 8.8/10**: good key-handle model, JSON/text helpers, async key iteration.

## Lowest-scoring surfaces

1. **FastAPI / ASGI — 8.0/10**: good framework shape, but needs broader package/middleware compatibility coverage.
2. **HTMLRewriter — 8.3/10**: strong wrapper, but still waiting on a real Python-native HTMLRewriter binding.
