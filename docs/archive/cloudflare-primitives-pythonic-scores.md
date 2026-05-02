# Cloudflare Primitive API Surface Pythonic Scores

Last reviewed: 2026-05-02. Scores are out of **10** and use [`pythonic-rubric.md`](../api/pythonic-rubric.md).

This scores the **API surface we currently expose in the examples**, not Cloudflare's underlying JavaScript APIs.

| Cloudflare primitive / surface | Example | Pythonic score | API surface summary | Main gaps |
|---|---|---:|---|---|
| Workers request/response | `examples/start/hello-worker` | 8.0 | Thin `WorkerEntrypoint`, localized response helper. | Shared response module; richer request parsing helper. |
| R2 object storage | `examples/storage-data/r2-object-storage` | 9.25 | `R2Bucket`, `R2ObjectRef`, typed metadata/options, `read_*`/`write_*`, `iter_objects`, multipart `async with`, `.raw`. | More route tests; full object-handle docs for every advanced option. |
| Workers KV | `examples/storage-data/kv-namespace` | 8.8 | `KVNamespace`, `KVKey`, text/JSON helpers, `exists`, `delete`, `list`, `iter_keys`; verifier covers text, JSON, list, delete. | Metadata/cache/expiration result modeling; deployed namespace verification. |
| FastAPI / ASGI on Workers | `examples/start/fastapi-worker` | 8.0 | Ordinary FastAPI app plus small ASGI adapter in `fetch`. | More Pyodide/package compatibility guidance. |
| D1 database | `examples/storage-data/d1-database` | 8.9 | `D1Database`, `D1Statement`, `statement`, `all`, `one`, `one_as`, typed row dataclass, parameter binding, indexed query plan route, D1 null conversion. | Migrations helper, transactions/batches, retry helpers. |
| Python package / LangChain boundary | `examples/ai-agents/langchain-style-chain` | 8.1 | Typed LCEL-style prompt chain with `PromptInput`, `PromptOutput`, `PromptChain`, service boundary, and local verifier. | Add real LangChain package compatibility when Pyodide support is sufficient. |
| Workers Assets | `examples/start/static-assets` | 9.0 | Teaches bypassing Python for static assets; dynamic `/api/status` route remains tiny and verified separately. | Cache/header assertions and SPA/not-found routing examples. |
| Durable Objects | `examples/state-events/durable-object-counter` | 8.6 | Named Durable Object counter, namespace wrapper, typed `CounterRef`, verified reset/increment/read across isolated names. | Concurrent increment checks; storage wrapper. |
| Cron triggers | `examples/state-events/cron-trigger` | 8.5 | `ScheduledEventInfo`, `ScheduledRunResult`, `ScheduledJob` service object and scheduled handler. | Persisted side-effect verification. |
| Workers AI | `examples/ai-agents/workers-ai-inference` | 8.7 | `AIService`, typed request dataclass, native dict response, deterministic local verifier. | Model-specific helpers; remote AI runtime check. |
| Queues | `examples/state-events/queues-producer-consumer` | 8.7 | `QueueService`, `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, explicit ack/retry handling, and deterministic consumer harness. | Real queue delivery verifier; dead-letter queue example. |
| Workflows | `examples/state-events/workflows-pipeline` | 8.5 | Workflow entrypoint, `WorkflowService.start/status`, durable steps, deterministic status verifier. | Real Workflow runtime status verification; richer typed event payloads. |
| HTMLRewriter | `examples/network-edge/htmlrewriter-opengraph` | 8.3 | Metadata dataclass, escaped transformation wrapper, and executable HTML response shape. | Real Python-native `HTMLRewriter` wrapper with element handlers when available. |
| Binary responses | `examples/streaming/binary-response` | 8.2 | Dependency-free PNG bytes and binary response with content-type and PNG signature verification. | Typed query params, validation, cache/R2 integration. |
| Service bindings / RPC | `examples/network-edge/service-bindings-rpc` | 8.3 | Python RPC method, TS client service binding, and local provider verifier. | Full two-worker verifier; typed request/response dataclasses. |
| Outbound WebSockets | `examples/network-edge/outbound-websocket-consumer` | 8.2 | Durable Object-owned outbound socket, alarms, Pyodide `create_proxy` boundary, deterministic status verifier. | Deterministic fake stream messages; higher-level session object. |
| Durable Objects + WebSockets | `examples/state-events/durable-object-chatroom` | 8.5 | Room-per-Durable-Object, browser client, WebSocket hibernation API, persisted message history, deterministic room verifier. | Automated WebSocket broadcast verifier; `ChatSession` abstraction. |
| Browser Rendering | `examples/network-edge/browser-rendering-screenshot` | 8.2 | `ScreenshotRequest`, `ScreenshotResult`, REST client, deterministic demo transport. | Content/PDF/scrape helpers and remote verifier. |
| Email Workers | `examples/network-edge/email-worker-router` | 8.3 | `IncomingEmail`, `EmailDecision`, routing policy, HTTP fixture verifier. | Reply/SendEmail/MIME helpers and deployed routing verifier. |
| AI Gateway | `examples/ai-agents/ai-gateway-chat` | 8.4 | OpenAI-compatible `ChatRequest`, `ChatMessage`, `ChatChoice`, gateway and demo transports. | Caching/rate-limit metadata and remote verifier. |
| R2 Data Catalog | `examples/storage-data/r2-data-catalog` | 8.3 | `Namespace`, `TableRef`, Iceberg REST client, deterministic catalog fixture. | PyIceberg create/append/read and remote verifier. |
| Hyperdrive | `examples/storage-data/hyperdrive-postgres` | 8.4 | `HyperdriveConfig`, `PostgresQuery`, `PostgresResult`, production/demo client split. | Real Postgres client wiring and remote verifier. |
| Agents SDK | `examples/ai-agents/agents-sdk-tools` | 8.6 | Typed agent messages, tool calls, run results, deterministic tools, Durable Object session routing. | Streaming responses and direct Agents SDK interop as Python support matures. |
| Streaming composition | `examples/streaming/gutenberg-stream-composition` | 8.8 | Typed byte/text/line streams, JSONL reader, batches, checkpoints, AI/agent/WebSocket event streams. | Lift helpers into a shared package and use real R2 body streams. |

## Current average

Current average across these API surfaces: **8.5 / 10**.

## Highest-scoring surfaces

1. **R2 — 9.25/10**: best layered API: friendly object handles, platform vocabulary, typed options, iteration, context manager lifecycle, escape hatch.
2. **Workers Assets — 8.9/10**: Pythonic because it avoids unnecessary Python work.
3. **KV — 8.8/10**: good key-handle model, JSON/text helpers, async key iteration.

## Lowest-scoring surfaces

1. **FastAPI / ASGI — 8.0/10**: good framework shape, but needs broader package/middleware compatibility coverage.
2. **HTMLRewriter — 8.3/10**: strong wrapper, but still waiting on a real Python-native HTMLRewriter binding.
