# Cloudflare Primitive API Surface Pythonic Scores

Last reviewed: 2026-05-01. Scores are out of **10** and use [`pythonic-rubric.md`](pythonic-rubric.md).

This scores the **API surface we currently expose in the examples**, not Cloudflare's underlying JavaScript APIs.

| Cloudflare primitive / surface | Example | Pythonic score | API surface summary | Main gaps |
|---|---|---:|---|---|
| Workers request/response | `workers-01-hello` | 8.0 | Thin `WorkerEntrypoint`, localized response helper. | Shared response module; richer request parsing helper. |
| R2 object storage | `r2-01` | 9.25 | `R2Bucket`, `R2ObjectRef`, typed metadata/options, `read_*`/`write_*`, `iter_objects`, multipart `async with`, `.raw`. | More route tests; full object-handle docs for every advanced option. |
| Workers KV | `kv-02-binding` | 8.8 | `KVNamespace`, `KVKey`, text/JSON helpers, `exists`, `delete`, `list`, `iter_keys`; verifier covers text, JSON, list, delete. | Metadata/cache/expiration result modeling; deployed namespace verification. |
| FastAPI / ASGI on Workers | `fastapi-03-framework` | 8.0 | Ordinary FastAPI app plus small ASGI adapter in `fetch`. | More Pyodide/package compatibility guidance. |
| D1 database | `d1-04-query` | 8.7 | `D1Database`, `D1Statement`, `statement`, `all`, `one`, `one_as`, typed row dataclass, parameter binding, D1 null conversion. | Migrations helper, transactions/batches, retry helpers. |
| Python package / LangChain boundary | `ai-05-langchain` | 6.75 | Service boundary shape around package orchestration. | Needs a real verified LangChain-compatible workload or replacement. |
| Workers Assets | `assets-06-static-assets` | 8.9 | Teaches bypassing Python for static assets; dynamic `/api/status` route remains tiny. | Cache/header assertions and SPA/not-found routing examples. |
| Durable Objects | `durable-objects-07-counter` | 8.6 | Named Durable Object counter, namespace wrapper, typed `CounterRef`, verified reset/increment/read across isolated names. | Concurrent increment checks; storage wrapper. |
| Cron triggers | `scheduled-08-cron` | 8.0 | `ScheduledJob` service object and scheduled handler. | Typed scheduled event wrapper; verifier for scheduled endpoint. |
| Workers AI | `workers-ai-09-inference` | 8.25 | `AIService`, typed request dataclass, native dict response. | Typed response models; model-specific helpers; verified AI runtime check. |
| Queues | `queues-16-producer-consumer` | 8.5 | `QueueService`, `QueueJob`, `QueueSendOptions`, `QueueMessage`, `QueueBatchResult`, and explicit ack/retry handling. | Consumer processing verifier; dead-letter queue example. |
| Workflows | `workflows-10-pipeline` | 7.75 | Workflow entrypoint, `WorkflowService.start/status`, durable steps. | `WorkflowInstance` handle; verified status flow; richer typed event payloads. |
| HTMLRewriter | `htmlrewriter-11-opengraph` | 7.75 | Metadata dataclass and executable HTML response shape. | Real `HTMLRewriter` wrapper with element handlers and JS boundary notes. |
| Binary responses / Pillow | `images-12-generation` | 8.0 | Simple Pillow PNG generation and binary response. | Typed query params, validation, cache/R2 integration. |
| Service bindings / RPC | `service-bindings-13-rpc` | 8.0 | Python RPC method and TS client service binding. | One-command verifier; typed request/response dataclasses. |
| Outbound WebSockets | `websockets-14-stream-consumer` | 7.75 | Durable Object-owned outbound socket, alarms, Pyodide `create_proxy` boundary. | Deterministic local fake stream; higher-level session object. |
| Durable Objects + WebSockets | `durable-objects-15-chatroom` | 8.0 | Room-per-Durable-Object, browser client, WebSocket hibernation API, message history. | Automated WebSocket verifier; `ChatSession` abstraction. |

## Current average

Current average across these API surfaces: **8.2 / 10**.

## Highest-scoring surfaces

1. **R2 — 9.25/10**: best layered API: friendly object handles, platform vocabulary, typed options, iteration, context manager lifecycle, escape hatch.
2. **Workers Assets — 8.9/10**: Pythonic because it avoids unnecessary Python work.
3. **KV — 8.8/10**: good key-handle model, JSON/text helpers, async key iteration.

## Lowest-scoring surfaces

1. **LangChain/package orchestration — 6.75/10**: not yet a real enough workload.
2. **Workflows / HTMLRewriter / outbound WebSockets — 7.75/10**: runnable shapes exist, but each needs a fuller Pythonic wrapper and deterministic verification.
